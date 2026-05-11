import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("papers")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_papers(self, papers: List[Dict[str, Any]]):
        for paper in papers:
            text = paper['title'] + " " + paper.get('abstract', '')
            embedding = self.model.encode(text).tolist()
            self.collection.add(
                documents=[text],
                embeddings=[embedding],
                ids=[paper['url']]
            )

    def search(self, query: str, n=5):
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n
        )
        return results['documents'][0] if results['documents'] else []