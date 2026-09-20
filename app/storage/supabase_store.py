from typing import List, Tuple, Dict, Any, Optional
from app.models.chunk import Chunk, ChunkMetadata
from app.models.document import ElementType
from app.storage.base import VectorStore
from app.core.supabase_client import supabase_manager
from app.core.logging import logger


class SupabaseVectorStore(VectorStore):
    """
    Supabase pgvector implementation of VectorStore interface.
    Uses Supabase RPC 'match_document_chunks' for vector similarity search.
    """

    def __init__(self):
        self.manager = supabase_manager

    def add_chunks(self, chunks: List[Chunk]):
        if not chunks:
            return

        if not self.manager.is_connected or not self.manager.client:
            logger.warning("Supabase client not connected. Cannot insert chunks into Supabase.")
            return

        records = [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.metadata.document_id,
                "file_id": c.metadata.file_id,
                "file_name": c.metadata.file_name,
                "page_number": c.metadata.page_number,
                "section": c.metadata.section or "",
                "element_type": c.metadata.element_type.value,
                "content": c.content,
                "parent_element_id": c.metadata.parent_element_id or "",
                "gdrive_url": c.metadata.gdrive_url or "",
                "image_path": c.metadata.image_path or "",
                "embedding": c.embedding,
            }
            for c in chunks
        ]

        try:
            self.manager.client.table("document_chunks").upsert(records).execute()
            logger.info(f"Indexed {len(chunks)} chunks in Supabase pgvector table 'document_chunks'.")
        except Exception as e:
            logger.error(f"Error inserting chunks into Supabase: {e}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 20,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        if not self.manager.is_connected or not self.manager.client:
            return []

        filter_file_id = filter_dict.get("file_id") if filter_dict else None

        try:
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.0,
                "match_count": top_k,
                "filter_file_id": filter_file_id
            }
            response = self.manager.client.rpc("match_document_chunks", rpc_params).execute()
            rows = response.data or []

            matched_chunks = []
            for row in rows:
                c_meta = ChunkMetadata(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    file_id=row["file_id"],
                    file_name=row["file_name"],
                    page_number=row["page_number"],
                    section=row.get("section"),
                    element_type=ElementType(row["element_type"]),
                    parent_element_id=row.get("parent_element_id"),
                    gdrive_url=row.get("gdrive_url"),
                    image_path=row.get("image_path")
                )
                chunk = Chunk(
                    chunk_id=row["chunk_id"],
                    content=row["content"],
                    metadata=c_meta,
                    embedding=query_embedding
                )
                similarity = float(row.get("similarity", 0.0))
                matched_chunks.append((chunk, similarity))

            return matched_chunks
        except Exception as e:
            logger.error(f"Error executing Supabase vector search: {e}")
            return []

    def delete_document(self, document_id: str):
        if not self.manager.is_connected or not self.manager.client:
            return
        try:
            self.manager.client.table("document_chunks").delete().eq("document_id", document_id).execute()
            logger.info(f"Deleted document {document_id} chunks from Supabase.")
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from Supabase: {e}")

    def clear(self):
        if not self.manager.is_connected or not self.manager.client:
            return
        try:
            self.manager.client.table("document_chunks").delete().neq("chunk_id", "").execute()
        except Exception as e:
            logger.error(f"Error clearing Supabase document_chunks table: {e}")
