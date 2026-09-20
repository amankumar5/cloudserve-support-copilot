from typing import List, Tuple, Dict, Any, Optional
from app.models.chunk import Chunk
from app.embeddings.service import embedding_service
from app.storage.chroma_store import vector_store
from app.retrieval.bm25 import bm25_engine
from app.core.config import settings
from app.core.logging import logger


class HybridRetriever:
    """
    Hybrid Retriever combining Dense Vector Search and BM25 Sparse Search via Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, alpha: float = settings.HYBRID_ALPHA, rrf_k: int = 60):
        self.alpha = alpha
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        # 1. Dense Vector Search
        query_emb = embedding_service.embed_query(query)
        vector_results = vector_store.search(query_embedding=query_emb, top_k=top_k, filter_dict=filter_dict)

        # 2. Sparse BM25 Search
        bm25_results = bm25_engine.search(query=query, top_k=top_k, filter_dict=filter_dict)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Chunk] = {}

        # Process vector ranks
        for rank, (chunk, score) in enumerate(vector_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + self.alpha * (1.0 / (self.rrf_k + rank + 1))

        # Process BM25 ranks
        for rank, (chunk, score) in enumerate(bm25_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 - self.alpha) * (1.0 / (self.rrf_k + rank + 1))

        # Sort combined results
        fused_results = [(chunk_map[cid], score) for cid, score in rrf_scores.items()]
        fused_results.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Hybrid retrieval for '{query}' returned {len(fused_results)} fused candidates.")
        return fused_results[:top_k]


hybrid_retriever = HybridRetriever()
