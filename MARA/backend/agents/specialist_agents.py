import asyncio
import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from .state import AgentState, MAX_ITERATIONS, CONFIDENCE_THRESHOLD
from ..tools.academic_tools import search_papers
from ..memory.vector_store import get_vector_store

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
TOP_K_PAPERS = 5

@lru_cache(maxsize=1)
def get_model() -> ChatGroq:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set. Add it to backend/.env")
    return ChatGroq(model=MODEL_NAME, max_tokens=4096, temperature=0.3, max_retries=3)

async def ask(prompt: str) -> str:
    response = await get_model().ainvoke(prompt)
    # `text` is a method in langchain-core 0.3 and a property (a str) in 1.x
    text = response.text if isinstance(response.text, str) else response.text()
    # some models emit stray control characters such as \x00
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(text))

def parse_score(text: str, label: str, default: float) -> float:
    # tolerate markdown emphasis such as **CONFIDENCE:** 0.8 and use the last occurrence
    matches = re.findall(rf'{label}[*_\s]*[:=][*_\s]*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    return float(matches[-1]) if matches else default

def format_papers(papers) -> str:
    return "\n".join(
        f"[{i + 1}] {p['title']} ({', '.join(p.get('authors', [])[:3]) or 'Unknown authors'}, {p.get('year') or 'n.d.'}) {p['url']}"
        for i, p in enumerate(papers)
    )

async def search_agent(state: AgentState) -> AgentState:
    search_query = state.get('search_query') or state['query']
    papers = await search_papers(search_query)
    if not papers:
        return {**state, 'papers': [], 'status': f'No papers found for "{search_query}"'}

    papers_text = "\n".join(f"{i}: Title: {p['title']}\nAbstract: {p['abstract'][:300]}..." for i, p in enumerate(papers))
    prompt = (
        f"Select the {TOP_K_PAPERS} most relevant papers for the research query: {state['query']}\n\n"
        f"Papers:\n{papers_text}\n\n"
        f"Reply with only the indices of the top {TOP_K_PAPERS} papers, separated by commas (e.g. 3, 0, 7, 1, 4)."
    )
    reply = await ask(prompt)
    indices = list(dict.fromkeys(int(i) for i in re.findall(r'\d+', reply) if int(i) < len(papers)))
    selected = [papers[i] for i in indices[:TOP_K_PAPERS]] or papers[:TOP_K_PAPERS]

    try:
        await asyncio.to_thread(get_vector_store().add_papers, selected)
    except Exception as e:
        print(f"Could not store papers in vector store: {e}")

    return {**state, 'papers': selected, 'status': f'Selected {len(selected)} of {len(papers)} papers'}

async def critique_paper(query: str, paper) -> dict:
    prompt = (
        f"Critique this paper for the research query: {query}\n"
        f"Title: {paper['title']}\nAbstract: {paper['abstract'] or 'No abstract available.'}\n\n"
        "Give a brief critique of its relevance, methodology and limitations. "
        "End with a final line in the form 'SCORE: <1-10>'."
    )
    critique = await ask(prompt)
    return {'paper': paper['title'], 'critique': critique, 'score': parse_score(critique, 'SCORE', 5.0)}

async def critic_agent(state: AgentState) -> AgentState:
    critiques = await asyncio.gather(*(critique_paper(state['query'], p) for p in state['papers']))
    return {**state, 'critiques': list(critiques), 'status': f'Critiqued {len(critiques)} papers'}

async def synthesis_agent(state: AgentState) -> AgentState:
    if not state['papers']:
        return {**state, 'synthesis': 'No papers were found for this query.', 'confidence_score': 0.0,
                'status': 'Synthesis skipped, no papers'}

    papers_text = "\n\n".join(
        f"[{i + 1}] {p['title']}\nAbstract: {p['abstract'][:800]}\nCritique: {c['critique']}"
        for i, (p, c) in enumerate(zip(state['papers'], state['critiques']))
    )
    prompt = (
        f"Synthesize the findings from these papers for the research query: {state['query']}\n\n{papers_text}\n\n"
        "Cite papers by their bracketed number, e.g. [2]. "
        "End with a final line in the form 'CONFIDENCE: <0.0-1.0>' rating how well the evidence answers the query."
    )
    synthesis = await ask(prompt)
    # an unparseable score counts as uncertain, so the reflection step can decide to search again
    confidence = min(max(parse_score(synthesis, 'CONFIDENCE', 0.5), 0.0), 1.0)
    return {**state, 'synthesis': synthesis, 'confidence_score': confidence, 'status': 'Synthesis completed'}

async def reflection_agent(state: AgentState) -> AgentState:
    if state['confidence_score'] >= CONFIDENCE_THRESHOLD or state['iteration'] >= MAX_ITERATIONS:
        return {**state, 'status': 'Confidence sufficient' if state['confidence_score'] >= CONFIDENCE_THRESHOLD
                else 'Max iterations reached'}

    prompt = (
        f"A literature search for the research query '{state['query']}' used the search terms "
        f"'{state['search_query']}' and produced a low-confidence synthesis:\n\n{state['synthesis'][:1500]}\n\n"
        "Suggest a better academic search query (a few keywords) to find more relevant papers. "
        "Reply with only the new search query."
    )
    lines = (await ask(prompt)).strip().splitlines()
    new_query = (lines[0].strip().strip('"*') if lines else '')[:200] or state['query']
    return {**state, 'search_query': new_query, 'iteration': state['iteration'] + 1,
            'status': f'Reflecting, low confidence. Searching again for "{new_query}"'}

async def writer_agent(state: AgentState) -> AgentState:
    prompt = (
        f"Write a well-structured markdown research report on the query: {state['query']}\n\n"
        f"Synthesis:\n{state['synthesis']}\n\nPapers:\n{format_papers(state['papers'])}\n\n"
        "Cite papers inline by their bracketed number and end with a References section listing each paper with its URL."
    )
    report = await ask(prompt)
    return {**state, 'report': report, 'status': 'Report written'}

async def hypothesis_agent(state: AgentState) -> AgentState:
    prompt = (
        f"Based on this synthesis for the research query '{state['query']}':\n{state['synthesis']}\n\n"
        "Identify research gaps and propose new testable hypotheses. "
        "Reply with a numbered list, one hypothesis per line, each ending with '(confidence: <0.0-1.0>)'."
    )
    reply = await ask(prompt)
    hypotheses = []
    for line in reply.splitlines():
        match = re.match(r'\s*(?:\d+[.)]|[-*])\s+(.*)', line)
        if not match:
            continue
        text = match.group(1)
        confidence = parse_score(text, r'\(?confidence', 0.5)
        text = re.sub(r'\s*\(?[*_]*confidence[*_\s]*[:=][*_\s]*\d+(?:\.\d+)?[*_]*\)?\s*$', '', text, flags=re.IGNORECASE)
        # the UI shows plain text, so drop markdown emphasis and "Hypothesis 1:" labels
        text = re.sub(r'^\s*hypothesis\s*\d*\s*:\s*', '', text.replace('*', ''), flags=re.IGNORECASE).strip()
        hypotheses.append({'hypothesis': text, 'confidence': min(max(confidence, 0.0), 1.0)})
    return {**state, 'hypotheses': hypotheses, 'status': 'Hypotheses generated'}
