"""Retrieve the most relevant knowledge-base entries for a message.

Uses sentence-transformers + ChromaDB when installed (multilingual, local, free).
Falls back to token overlap so the project still runs without heavy dependencies.
"""
import re

from .engine import load_kb


class Retriever:
    def __init__(self, kb=None):
        self.kb = kb or load_kb()
        self.docs = [f'{k["label"]}: {k["meaning"]} ({k["pattern"]})' for k in self.kb]
        self.col = self.model = None
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            self.col = chromadb.Client().create_collection("kb")
            self.col.add(ids=[str(i) for i in range(len(self.docs))],
                         embeddings=self.model.encode(self.docs).tolist(), documents=self.docs)
        except Exception:
            self.col = None

    def retrieve(self, text: str, k: int = 3) -> list[str]:
        if self.col is not None:
            return self.col.query(query_embeddings=self.model.encode([text]).tolist(), n_results=k)["documents"][0]
        words = set(re.findall(r"\w+", text.lower()))
        scored = sorted(self.docs, key=lambda d: -len(words & set(re.findall(r"\w+", d.lower()))))
        return scored[:k]
