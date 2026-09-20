from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from app.models.chunk import Chunk


class VectorStore(ABC):
    """
    Abstract Base Vector Store interface.
    Allows replacing ChromaDB with PgVector, Qdrant, or Pinecone without altering retrieval logic.
    """

    @abstractmethod
    def add_chunks(self, chunks: List[Chunk]):
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 20,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        pass

    @abstractmethod
    def delete_document(self, document_id: str):
        pass

    @abstractmethod
    def clear(self):
        pass
