import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from models import FAQEntry, SearchResult

class FAQIndex:
    def __init__(self, faq_text: str):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.entries = self._parse(faq_text)
        self.embeddings = self.model.encode([e.text for e in self.entries])

    def _parse(self, faq_text: str) -> list[FAQEntry]:
        raw = re.split(r'\n(?=\d+\.)', faq_text.strip())
        entries = []
        for i, entry in enumerate(raw):
            entry = entry.strip()
            if not entry:
                continue
            # Try the strict "1. **Question**\nAnswer" form first, then fall
            # back to "1. Question\nAnswer" without bold markers.
            match = re.match(r'\d+\.\s*\*\*(.+?)\*\*\s*\n+(.+)', entry, re.DOTALL)
            if not match:
                match = re.match(r'\d+\.\s*(.+?)\n+(.+)', entry, re.DOTALL)
            if not match:
                # Skip malformed entries instead of crashing.
                continue
            q = match.group(1).strip()
            a = match.group(2).strip()
            if not q or not a:
                continue
            entries.append(FAQEntry(id=i+1, question=q, answer=a, text=f"Question: {q}\nAnswer: {a}"))
        return entries

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        query_emb = self.model.encode(query)
        scores = cosine_similarity([query_emb], self.embeddings)[0]
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(
                entry_id=self.entries[i].id,
                question=self.entries[i].question,
                answer=self.entries[i].answer,
                score=float(scores[i])
            ) for i in top_idx
        ]
