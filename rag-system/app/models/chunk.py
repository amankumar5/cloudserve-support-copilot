from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.document import ElementType


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    file_id: str
    file_name: str
    page_number: int
    section: Optional[str] = None
    element_type: ElementType
    parent_element_id: Optional[str] = None
    gdrive_url: Optional[str] = None
    image_path: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    chunk_id: str
    content: str
    metadata: ChunkMetadata
    embedding: Optional[list[float]] = None
