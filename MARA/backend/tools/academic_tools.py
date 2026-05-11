import aiohttp
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

async def search_semantic_scholar(query: str) -> List[Dict[str, Any]]:
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=10&fields=title,abstract,authors,year,url"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    papers = data.get('data', [])
                    for p in papers:
                        p['source'] = 'Semantic Scholar'
                    return papers
                else:
                    return []
        except Exception as e:
            print(f"Error searching Semantic Scholar: {e}")
            return []

async def search_arxiv(query: str) -> List[Dict[str, Any]]:
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=10"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    root = ET.fromstring(xml_data)
                    papers = []
                    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                        title = entry.find('{http://www.w3.org/2005/Atom}title').text or ""
                        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text or ""
                        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author') if author.find('{http://www.w3.org/2005/Atom}name') is not None]
                        published = entry.find('{http://www.w3.org/2005/Atom}published').text or ""
                        year = published[:4] if published else ""
                        paper_url = entry.find('{http://www.w3.org/2005/Atom}id').text or ""
                        papers.append({
                            'title': title,
                            'abstract': summary,
                            'authors': authors,
                            'year': year,
                            'url': paper_url,
                            'source': 'arXiv'
                        })
                    return papers
                else:
                    return []
        except Exception as e:
            print(f"Error searching arXiv: {e}")
            return []

async def search_papers(query: str) -> List[Dict[str, Any]]:
    ss_papers = await search_semantic_scholar(query)
    arxiv_papers = await search_arxiv(query)
    return ss_papers + arxiv_papers