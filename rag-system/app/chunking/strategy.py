import uuid
from typing import List
from app.models.document import Document, ElementType
from app.models.chunk import Chunk, ChunkMetadata
from app.core.logging import logger


class StructureAwareChunker:
    """
    Structure-Aware Chunking Strategy preserving tabular boundaries, diagram visual contexts,
    and heading hierarchies.
    """

    def __init__(self, max_chunk_chars: int = 1500, overlap_chars: int = 200):
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_document(self, doc: Document) -> List[Chunk]:
        chunks: List[Chunk] = []

        for page in doc.pages:
            current_section = f"Page {page.page_number}"
            text_accumulator = []
            text_accum_ids = []

            for elem in page.elements:
                # Update section heading
                if elem.element_type == ElementType.HEADING:
                    current_section = elem.content_text
                    # Flush accumulated text under previous heading
                    if text_accumulator:
                        chunks.extend(self._create_text_chunks(
                            doc=doc,
                            page_num=page.page_number,
                            section=current_section,
                            text_lines=text_accumulator,
                            parent_id=text_accum_ids[0] if text_accum_ids else elem.element_id
                        ))
                        text_accumulator = []
                        text_accum_ids = []

                # Tables: Keep intact as a single complete chunk
                elif elem.element_type == ElementType.TABLE:
                    # Flush pending text
                    if text_accumulator:
                        chunks.extend(self._create_text_chunks(
                            doc=doc,
                            page_num=page.page_number,
                            section=current_section,
                            text_lines=text_accumulator,
                            parent_id=text_accum_ids[0]
                        ))
                        text_accumulator = []
                        text_accum_ids = []

                    table_chunk_content = f"Section: {current_section}\nDocument: {doc.file_name} (Page {page.page_number})\n\n{elem.content_text}"
                    cid = f"{elem.element_id}_chk"
                    c_meta = ChunkMetadata(
                        chunk_id=cid,
                        document_id=doc.document_id,
                        file_id=doc.file_id,
                        file_name=doc.file_name,
                        page_number=page.page_number,
                        section=current_section,
                        element_type=ElementType.TABLE,
                        parent_element_id=elem.element_id,
                        gdrive_url=doc.gdrive_url,
                        image_path=elem.image_path
                    )
                    chunks.append(Chunk(chunk_id=cid, content=table_chunk_content, metadata=c_meta))

                # Diagrams/Images: Keep intact as a single complete visual chunk
                elif elem.element_type in [ElementType.DIAGRAM, ElementType.IMAGE]:
                    # Flush pending text
                    if text_accumulator:
                        chunks.extend(self._create_text_chunks(
                            doc=doc,
                            page_num=page.page_number,
                            section=current_section,
                            text_lines=text_accumulator,
                            parent_id=text_accum_ids[0]
                        ))
                        text_accumulator = []
                        text_accum_ids = []

                    diagram_chunk_content = f"Section: {current_section}\nDocument: {doc.file_name} (Page {page.page_number})\n\n{elem.content_text}"
                    cid = f"{elem.element_id}_chk"
                    c_meta = ChunkMetadata(
                        chunk_id=cid,
                        document_id=doc.document_id,
                        file_id=doc.file_id,
                        file_name=doc.file_name,
                        page_number=page.page_number,
                        section=current_section,
                        element_type=elem.element_type,
                        parent_element_id=elem.element_id,
                        gdrive_url=doc.gdrive_url,
                        image_path=elem.image_path
                    )
                    chunks.append(Chunk(chunk_id=cid, content=diagram_chunk_content, metadata=c_meta))

                # Text elements
                else:
                    text_accumulator.append(elem.content_text)
                    text_accum_ids.append(elem.element_id)

            # Flush remaining text on page
            if text_accumulator:
                chunks.extend(self._create_text_chunks(
                    doc=doc,
                    page_num=page.page_number,
                    section=current_section,
                    text_lines=text_accumulator,
                    parent_id=text_accum_ids[0] if text_accum_ids else None
                ))

        logger.info(f"Chunked document {doc.file_name} into {len(chunks)} structure-aware chunks.")
        return chunks

    def _create_text_chunks(
        self,
        doc: Document,
        page_num: int,
        section: str,
        text_lines: List[str],
        parent_id: str
    ) -> List[Chunk]:
        full_text = "\n\n".join(text_lines).strip()
        if not full_text:
            return []

        chunks: List[Chunk] = []
        start = 0

        while start < len(full_text):
            end = min(start + self.max_chunk_chars, len(full_text))
            chunk_slice = full_text[start:end].strip()

            cid = f"{doc.document_id}_p{page_num}_{uuid.uuid4().hex[:6]}"
            content_with_header = f"Section: {section}\nDocument: {doc.file_name} (Page {page_num})\n\n{chunk_slice}"

            c_meta = ChunkMetadata(
                chunk_id=cid,
                document_id=doc.document_id,
                file_id=doc.file_id,
                file_name=doc.file_name,
                page_number=page_num,
                section=section,
                element_type=ElementType.TEXT,
                parent_element_id=parent_id,
                gdrive_url=doc.gdrive_url
            )
            chunks.append(Chunk(chunk_id=cid, content=content_with_header, metadata=c_meta))

            if end >= len(full_text):
                break
            start += (self.max_chunk_chars - self.overlap_chars)

        return chunks


chunker = StructureAwareChunker()
