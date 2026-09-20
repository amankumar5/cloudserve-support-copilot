import re
from typing import List, Tuple, Dict, Any, Optional
from app.models.chunk import Chunk
from app.core.logging import logger


class BM25Engine:
    """
    BM25 Keyword Search Engine for exact keyword, technical code, and product name retrieval.
    """

    def __init__(self):
        self.chunks: List[Chunk] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25 = None
        self._is_indexed = False

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) > 1]

    def index_chunks(self, chunks: List[Chunk]):
        if not chunks:
            return

        self.chunks.extend(chunks)
        for c in chunks:
            self.corpus_tokens.append(self._tokenize(c.content))

        self._rebuild_index()

    def _rebuild_index(self):
        if not self.corpus_tokens:
            self._is_indexed = False
            return

        try:
            from rank_bm25 import BM25Okapi
            self.bm25 = BM25Okapi(self.corpus_tokens)
            self._is_indexed = True
            logger.info(f"BM25 index built with {len(self.chunks)} chunks.")
        except Exception as e:
            logger.warning(f"Failed loading rank_bm25: {e}. Falling back to simple keyword matching.")
            self._is_indexed = False

    def search(self, query: str, top_k: int = 20, filter_dict: Optional[Dict[str, Any]] = None) -> List[Tuple[Chunk, float]]:
        if not self.chunks:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scored_chunks: List[Tuple[Chunk, float]] = []

        if self._is_indexed and self.bm25:
            scores = self.bm25.get_scores(tokens)
            for idx, score in enumerate(scores):
                if score <= 0:
                    continue
                c = self.chunks[idx]

                if filter_dict:
                    match = True
                    for k, v in filter_dict.items():
                        val = getattr(c.metadata, k, None)
                        if val != v:
                            match = False
                            break
                    if not match:
                        continue

                scored_chunks.append((c, float(score)))
        else:
            # Fallback simple keyword frequency scorer
            query_set = set(tokens)
            for c in self.chunks:
                c_tokens = set(self._tokenize(c.content))
                matches = query_set.intersection(c_tokens)
                if matches:
                    score = len(matches) / float(len(query_set))
                    scored_chunks.append((c, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    def delete_document(self, document_id: str):
        indices_to_keep = [
            i for i, c in enumerate(self.chunks) if c.metadata.document_id != document_id
        ]
        self.chunks = [self.chunks[i] for i in indices_to_keep]
        self.corpus_tokens = [self.corpus_tokens[i] for i in indices_to_keep]
        self._rebuild_index()

    def clear(self):
        self.chunks.clear()
        self.corpus_tokens.clear()
        self.bm25 = None
        self._is_indexed = False


bm25_engine = BM25Engine()
