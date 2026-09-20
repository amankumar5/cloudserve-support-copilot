import uuid
from typing import List
from app.models.document import Document, Page, DocumentElement, ElementType
from app.parsing.base import BaseDocumentParser
from app.parsing.vision_analyzer import vision_analyzer
from app.core.logging import logger


class ImageParser(BaseDocumentParser):
    """
    Image Document Parser for standalone PNG, JPEG, WEBP images, diagrams, and screenshots.
    """

    def parse(self, file_path: str, file_id: str, file_name: str, gdrive_url: str = "") -> Document:
        logger.info(f"Parsing Image document: {file_name}")
        document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_id or file_name))

        vision_result = vision_analyzer.analyze_image(
            image_path=file_path,
            context_caption=f"Standalone Image document: {file_name}"
        )

        diag_text = (
            f"[Visual Element / Diagram: {file_name}]\n"
            f"Type: {vision_result.get('diagram_type', 'technical_diagram')}\n"
            f"Description: {vision_result.get('description', '')}\n"
        )
        if vision_result.get("components"):
            diag_text += f"Components: {', '.join(vision_result['components'])}\n"
        if vision_result.get("connections"):
            diag_text += f"Connections: {', '.join(vision_result['connections'])}\n"
        if vision_result.get("text_labels"):
            diag_text += f"Text Labels: {' | '.join(vision_result['text_labels'])}\n"

        img_elem = DocumentElement(
            element_id=f"{document_id}_img",
            element_type=ElementType.DIAGRAM,
            page_number=1,
            section_title="Image Document",
            content_text=diag_text.strip(),
            structured_data=vision_result,
            image_path=file_path
        )

        single_page = Page(
            page_number=1,
            elements=[img_elem],
            page_text=diag_text
        )

        doc = Document(
            document_id=document_id,
            file_name=file_name,
            file_id=file_id,
            mime_type="image/png",
            gdrive_url=gdrive_url,
            pages=[single_page],
            metadata={
                "pages_count": 1,
                "elements_count": 1
            }
        )
        logger.info(f"Successfully parsed standalone image {file_name}.")
        return doc
