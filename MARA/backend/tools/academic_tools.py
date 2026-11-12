import asyncio
import os
import aiohttp
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

ATOM = '{http://www.w3.org/2005/Atom}'
TIMEOUT = aiohttp.ClientTimeout(total=20)

async def search_semantic_scholar(session: aiohttp.ClientSession, query: str) -> List[Dict[str, Any]]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {'query': query, 'limit': 10, 'fields': 'title,abstract,authors,year,url'}
    # anonymous requests share a small rate limit and often get HTTP 429
    api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    headers = {'x-api-key': api_key} if api_key else {}
    try:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status != 200:
                print(f"Semantic Scholar returned HTTP {response.status}")
                return []
            data = await response.json()
            papers = []
            for p in data.get('data') or []:
                papers.append({
                    'title': (p.get('title') or '').strip(),
                    'abstract': p.get('abstract') or '',
                    'authors': [a.get('name', '') for a in p.get('authors') or []],
                    'year': str(p.get('year') or ''),
                    'url': p.get('url') or f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}",
                    'source': 'Semantic Scholar'
                })
            return papers
    except Exception as e:
        print(f"Error searching Semantic Scholar: {e}")
        return []

def _text(entry: ET.Element, tag: str) -> str:
    el = entry.find(ATOM + tag)
    return (el.text or '').strip() if el is not None else ''

async def search_arxiv(session: aiohttp.ClientSession, query: str) -> List[Dict[str, Any]]:
    url = "https://export.arxiv.org/api/query"
    params = {'search_query': f'all:{query}', 'start': 0, 'max_results': 10}
    try:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                print(f"arXiv returned HTTP {response.status}")
                return []
            root = ET.fromstring(await response.text())
            papers = []
            for entry in root.findall(ATOM + 'entry'):
                authors = [_text(a, 'name') for a in entry.findall(ATOM + 'author')]
                papers.append({
                    'title': ' '.join(_text(entry, 'title').split()),
                    'abstract': ' '.join(_text(entry, 'summary').split()),
                    'authors': [a for a in authors if a],
                    'year': _text(entry, 'published')[:4],
                    'url': _text(entry, 'id'),
                    'source': 'arXiv'
                })
            return papers
    except Exception as e:
        print(f"Error searching arXiv: {e}")
        return []

async def search_papers(query: str) -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        ss_papers, arxiv_papers = await asyncio.gather(
            search_semantic_scholar(session, query),
            search_arxiv(session, query)
        )
    # drop untitled entries and duplicates that appear in both sources
    seen = set()
    papers = []
    for p in ss_papers + arxiv_papers:
        key = p['title'].lower()
        if p['title'] and p['url'] and key not in seen:
            seen.add(key)
            papers.append(p)
    return papers
