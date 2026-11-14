"""
MotherlyPulse Grounded Clinical Passage Retriever
Indexes the 35 verified clinical evidence passages (WHO ANC 2016, WHO PNC 2022, FMOH 2019)
and performs grounded TF-IDF vector retrieval with n-gram keyword weighting.
"""

import os
import csv
import logging
from typing import Dict, Any, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

PASSAGES_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "MotherlyPulse_Data", "02_Passages", "passages.csv"
))


class ClinicalPassageRetriever:
    def __init__(self, passages_path: str = PASSAGES_PATH):
        self.passages_path = passages_path
        self.passages: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._load_and_index()

    def _load_and_index(self):
        if not os.path.exists(self.passages_path):
            logger.error(f"Passages file not found: {self.passages_path}")
            return

        with open(self.passages_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.passages = list(reader)

        if not self.passages:
            logger.warning("No passages loaded.")
            return

        # Build corpus with weighted topics, danger signs, and passage text
        corpus = []
        for p in self.passages:
            doc = (
                f"{p.get('topic', '')} {p.get('topic', '')} "
                f"{p.get('subtopic', '')} "
                f"{p.get('danger_signs_mentioned', '')} {p.get('danger_signs_mentioned', '')} "
                f"{p.get('passage_text', '')}"
            )
            corpus.append(doc)

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 1) -> List[Dict[str, Any]]:
        """
        Retrieves top_k matching passages for the query.
        Returns list of dicts with passage_id, topic, score, passage_text.
        """
        if not self.passages or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        # Rank indices by score descending
        ranked_indices = scores.argsort()[::-1][:top_k]

        results = []
        for idx in ranked_indices:
            p_dict = dict(self.passages[idx])
            p_dict["score"] = float(scores[idx])
            results.append(p_dict)
        return results

    def retrieve_passage_id(self, query: str) -> Optional[str]:
        """Returns the top-1 retrieved passage_id."""
        results = self.retrieve(query, top_k=1)
        if results and results[0]["score"] > 0:
            return results[0]["passage_id"]
        return self.passages[0]["passage_id"] if self.passages else None

    def retrieve_passage_text(self, query: str) -> Optional[str]:
        """Returns the top-1 retrieved passage_text."""
        results = self.retrieve(query, top_k=1)
        if results and results[0]["score"] > 0:
            return results[0].get("passage_text")
        return self.passages[0].get("passage_text") if self.passages else None

