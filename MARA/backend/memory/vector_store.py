import os
from functools import lru_cache
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer

DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db"))

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_PATH)
        self.collection = self.client.get_or_create_collection("papers")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_papers(self, papers: List[Dict[str, Any]]):
        if not papers:
            return
        texts = [p['title'] + " " + (p.get('abstract') or '') for p in papers]
        embeddings = self.model.encode(texts).tolist()
        # upsert so re-running a query doesn't fail on papers already stored
        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            ids=[p['url'] for p in papers],
            metadatas=[{'title': p['title'], 'source': p.get('source', ''), 'year': p.get('year', '')} for p in papers]
        )

    def search(self, query: str, n=5):
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n
        )
        return results['documents'][0] if results['documents'] else []

@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    # loading the embedding model is slow, so share one instance
    return VectorStore()
