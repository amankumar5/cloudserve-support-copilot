import os
import math
from typing import List, Tuple, Dict, Any, Optional
from app.models.chunk import Chunk, ChunkMetadata
from app.models.document import ElementType
from app.storage.base import VectorStore
from app.core.config import settings
from app.core.logging import logger


class ChromaVectorStore(VectorStore):
    """
    ChromaDB implementation of VectorStore interface.
    """
    def __init__(self, persist_dir: Optional[str] = None, collection_name: str = "multimodal_rag"):
        import chromadb
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: List[Chunk]):
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        embeddings = [c.embedding for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "chunk_id": c.metadata.chunk_id,
                "document_id": c.metadata.document_id,
                "file_id": c.metadata.file_id,
                "file_name": c.metadata.file_name,
                "page_number": c.metadata.page_number,
                "section": c.metadata.section or "",
                "element_type": c.metadata.element_type.value,
                "parent_element_id": c.metadata.parent_element_id or "",
                "gdrive_url": c.metadata.gdrive_url or "",
                "image_path": c.metadata.image_path or "",
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Indexed {len(chunks)} chunks in ChromaDB vector store.")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 20,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        where = filter_dict if filter_dict else None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )

        matched_chunks = []
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        for i in range(len(results["ids"][0])):
            cid = results["ids"][0][i]
            content = results["documents"][0][i]
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.0

            # Convert distance to similarity score
            similarity = 1.0 / (1.0 + distance)

            chunk_meta = ChunkMetadata(
                chunk_id=meta["chunk_id"],
                document_id=meta["document_id"],
                file_id=meta["file_id"],
                file_name=meta["file_name"],
                page_number=meta["page_number"],
                section=meta.get("section"),
                element_type=ElementType(meta["element_type"]),
                parent_element_id=meta.get("parent_element_id"),
                gdrive_url=meta.get("gdrive_url"),
                image_path=meta.get("image_path"),
            )
            c = Chunk(chunk_id=cid, content=content, metadata=chunk_meta, embedding=query_embedding)
            matched_chunks.append((c, similarity))

        return matched_chunks

    def delete_document(self, document_id: str):
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted document {document_id} chunks from ChromaDB.")
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from ChromaDB: {e}")

    def clear(self):
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(self.collection.name)
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {e}")


class InMemoryVectorStore(VectorStore):
    """
    In-memory fallback vector store implementation using cosine similarity.
    Useful for testing or light deployment environments.
    """
    def __init__(self):
        self.chunks: Dict[str, Chunk] = {}

    def add_chunks(self, chunks: List[Chunk]):
        for c in chunks:
            self.chunks[c.chunk_id] = c

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 20,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        scored = []
        for c in self.chunks.values():
            if filter_dict:
                match = True
                for k, v in filter_dict.items():
                    val = getattr(c.metadata, k, None)
                    if val != v:
                        match = False
                        break
                if not match:
                    continue

            score = self._cosine_similarity(query_embedding, c.embedding or [])
            scored.append((c, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def delete_document(self, document_id: str):
        to_delete = [cid for cid, c in self.chunks.items() if c.metadata.document_id == document_id]
        for cid in to_delete:
            del self.chunks[cid]

    def clear(self):
        self.chunks.clear()


def get_vector_store() -> VectorStore:
    vtype = settings.VECTOR_STORE_TYPE.lower()
    if vtype == "chroma":
        try:
            return ChromaVectorStore()
        except Exception as e:
            logger.warning(f"Failed initializing ChromaVectorStore: {e}. Falling back to InMemoryVectorStore.")
            return InMemoryVectorStore()
    return InMemoryVectorStore()


vector_store = get_vector_store()
