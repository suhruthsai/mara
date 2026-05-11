from langchain_anthropic import ChatAnthropic
from .state import AgentState
from ..tools.academic_tools import search_papers
from ..memory.vector_store import VectorStore
import os
import re

os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")

model = ChatAnthropic(model="claude-sonnet-4-20250514")

async def search_agent(state: AgentState) -> AgentState:
    papers = await search_papers(state['query'])
    # use Claude to select top 5
    papers_text = "\n".join([f"{i}: Title: {p['title']}\nAbstract: {p.get('abstract', '')[:200]}..." for i, p in enumerate(papers)])
    prompt = f"Select the top 5 most relevant papers for the research query: {state['query']}\n\nPapers:\n{papers_text}\n\nReturn the indices of the top 5 papers, separated by commas."
    response = model.invoke(prompt)
    indices = [int(i.strip()) for i in response.content.split(',') if i.strip().isdigit()]
    selected = [papers[i] for i in indices if i < len(papers)]
    vector_store = VectorStore()
    vector_store.add_papers(selected)
    return {**state, 'papers': selected, 'status': 'Papers searched and selected'}

async def critic_agent(state: AgentState) -> AgentState:
    critiques = []
    for paper in state['papers']:
        prompt = f"Critique this paper for the query {state['query']}:\nTitle: {paper['title']}\nAbstract: {paper.get('abstract', '')}\n\nProvide a score from 1-10 and a brief critique."
        response = model.invoke(prompt)
        critiques.append({'paper': paper['title'], 'critique': response.content})
    return {**state, 'critiques': critiques, 'status': 'Papers critiqued'}

async def synthesis_agent(state: AgentState) -> AgentState:
    papers_text = "\n".join([f"Title: {p['title']}\nCritique: {c['critique']}" for p, c in zip(state['papers'], state['critiques'])])
    prompt = f"Synthesize the findings from these papers for the query {state['query']}:\n{papers_text}\n\nProvide a synthesis and a confidence score from 0-1."
    response = model.invoke(prompt)
    synthesis = response.content
    # parse confidence
    confidence = 0.8  # default
    match = re.search(r'confidence[:\s]*(\d\.\d+)', synthesis.lower())
    if match:
        confidence = float(match.group(1))
    return {**state, 'synthesis': synthesis, 'confidence_score': confidence, 'status': 'Synthesis completed'}

async def writer_agent(state: AgentState) -> AgentState:
    prompt = f"Write a markdown report on the query {state['query']} based on the synthesis: {state['synthesis']}\nInclude citations to the papers."
    response = model.invoke(prompt)
    report = response.content
    return {**state, 'report': report, 'status': 'Report written'}

async def hypothesis_agent(state: AgentState) -> AgentState:
    prompt = f"Based on the synthesis: {state['synthesis']}, identify research gaps and generate new hypotheses for the query {state['query']}."
    response = model.invoke(prompt)
    hypotheses_text = response.content
    hypotheses = [{'hypothesis': h.strip(), 'confidence': 0.7} for h in hypotheses_text.split('\n') if h.strip()]
    return {**state, 'hypotheses': hypotheses, 'status': 'Hypotheses generated'}