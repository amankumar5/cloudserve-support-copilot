import os
from app.parsing.base import BaseDocumentParser
from app.parsing.pdf_parser import PDFParser
from app.parsing.docx_parser import DOCXParser
from app.parsing.pptx_parser import PPTXParser
from app.parsing.xlsx_parser import XLSXParser
from app.parsing.image_parser import ImageParser
from app.core.logging import logger


class ParserFactory:
    """
    Factory resolving file path / mime-type to appropriate DocumentParser implementation.
    """

    @staticmethod
    def get_parser(file_path: str, mime_type: str = "") -> BaseDocumentParser:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf" or mime_type == "application/pdf":
            return PDFParser()
        elif ext == ".docx" or "wordprocessingml" in mime_type:
            return DOCXParser()
        elif ext == ".pptx" or "presentationml" in mime_type:
            return PPTXParser()
        elif ext == ".xlsx" or "spreadsheetml" in mime_type:
            return XLSXParser()
        elif ext in [".png", ".jpg", ".jpeg", ".webp"] or "image/" in mime_type:
            return ImageParser()
        else:
            logger.warning(f"Unsupported extension {ext} / mime-type {mime_type}. Defaulting to PDFParser.")
            return PDFParser()


parser_factory = ParserFactory()
