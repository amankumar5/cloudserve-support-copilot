from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ElementType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    DIAGRAM = "diagram"
    IMAGE = "image"
    LIST_ITEM = "list_item"
    CAPTION = "caption"
    FOOTNOTE = "footnote"


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class DocumentElement(BaseModel):
    element_id: str
    element_type: ElementType
    page_number: int
    section_title: Optional[str] = None
    content_text: str
    structured_data: Optional[Dict[str, Any]] = None  # e.g., table headers/rows matrix or diagram component graph
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    parent_id: Optional[str] = None


class Page(BaseModel):
    page_number: int
    elements: List[DocumentElement] = Field(default_factory=list)
    page_text: str = ""


class Document(BaseModel):
    document_id: str
    file_name: str
    file_id: str
    mime_type: str
    gdrive_url: Optional[str] = None
    modified_time: Optional[str] = None
    md5_checksum: Optional[str] = None
    pages: List[Page] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ingested_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
