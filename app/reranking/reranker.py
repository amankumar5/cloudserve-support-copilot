from typing import List, Tuple
from app.models.chunk import Chunk
from app.core.config import settings
from app.core.logging import logger


class Reranker:
    """
    Reranker re-scoring candidate chunks using FlashRank local cross-encoder.
    """

    def __init__(self):
        self.ranker = None
        self._init_ranker()

    def _init_ranker(self):
        if not settings.USE_RERANKER:
            return
        try:
            from flashrank import Ranker
            self.ranker = Ranker(model_name="ms-marco-MiniLM-L-6-v2")
            logger.info("FlashRank Reranker initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not load FlashRank reranker: {e}. Using RRF score order fallback.")
            self.ranker = None

    def rerank(self, query: str, candidates: List[Tuple[Chunk, float]], top_k: int = settings.TOP_K_RERANKED) -> List[Tuple[Chunk, float]]:
        if not candidates:
            return []

        if not self.ranker:
            return candidates[:top_k]

        try:
            passages = [
                {"id": idx, "text": chunk.content}
                for idx, (chunk, score) in enumerate(candidates)
            ]
            from flashrank import RerankRequest
            req = RerankRequest(query=query, passages=passages)
            results = self.ranker.rerank(req)

            reranked: List[Tuple[Chunk, float]] = []
            for item in results[:top_k]:
                orig_idx = item["id"]
                score = float(item["score"])
                reranked.append((candidates[orig_idx][0], score))

            logger.info(f"Reranked {len(candidates)} candidates down to {len(reranked)} top chunks.")
            return reranked

        except Exception as e:
            logger.warning(f"Error during reranking execution: {e}. Returning original candidates.")
            return candidates[:top_k]


reranker = Reranker()
