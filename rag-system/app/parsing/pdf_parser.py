import os
import uuid
import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict, Any, Optional
from app.models.document import Document, Page, DocumentElement, ElementType, BoundingBox
from app.parsing.base import BaseDocumentParser
from app.parsing.vision_analyzer import vision_analyzer
from app.core.config import settings
from app.core.logging import logger


class PDFParser(BaseDocumentParser):
    """
    Multimodal PDF Parser combining PyMuPDF layout analysis, pdfplumber table extraction,
    and Gemini Vision diagram understanding.
    """

    def parse(self, file_path: str, file_id: str, file_name: str, gdrive_url: str = "") -> Document:
        logger.info(f"Parsing PDF document: {file_name}")
        document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_id or file_name))
        doc_pages: List[Page] = []
        total_elements = 0

        # Open with PyMuPDF for text/images and pdfplumber for tables
        fitz_doc = fitz.open(file_path)

        with pdfplumber.open(file_path) as plumber_doc:
            for page_idx, fitz_page in enumerate(fitz_doc):
                page_num = page_idx + 1
                plumber_page = plumber_doc.pages[page_idx] if page_idx < len(plumber_doc.pages) else None

                page_elements: List[DocumentElement] = []
                current_section = f"Page {page_num}"

                # 1. Extract Tables using pdfplumber
                table_bboxes = []
                if plumber_page:
                    extracted_tables = plumber_page.extract_tables()
                    tables_with_pos = plumber_page.find_tables()

                    for tbl_idx, table_obj in enumerate(tables_with_pos):
                        raw_table = extracted_tables[tbl_idx] if tbl_idx < len(extracted_tables) else None
                        if not raw_table or not any(raw_table):
                            continue

                        # Record table bounding box to avoid duplicate text extraction
                        table_bboxes.append(table_obj.bbox)

                        # Clean table cells
                        clean_rows = []
                        for row in raw_table:
                            clean_rows.append([cell.strip().replace("\n", " ") if cell else "" for cell in row])

                        if not clean_rows or not clean_rows[0]:
                            continue

                        headers = clean_rows[0]
                        data_rows = clean_rows[1:]

                        # Build Markdown Table representation
                        md_lines = ["| " + " | ".join(headers) + " |"]
                        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                        for r in data_rows:
                            md_lines.append("| " + " | ".join(r) + " |")
                        table_md = "\n".join(md_lines)

                        tbl_elem = DocumentElement(
                            element_id=f"{document_id}_p{page_num}_tbl{tbl_idx}",
                            element_type=ElementType.TABLE,
                            page_number=page_num,
                            section_title=current_section,
                            content_text=table_md,
                            structured_data={
                                "headers": headers,
                                "rows": data_rows,
                                "row_count": len(data_rows),
                                "column_count": len(headers)
                            },
                            bbox=BoundingBox(
                                x0=table_obj.bbox[0],
                                y0=table_obj.bbox[1],
                                x1=table_obj.bbox[2],
                                y1=table_obj.bbox[3]
                            )
                        )
                        page_elements.append(tbl_elem)
                        total_elements += 1

                # 2. Extract Text Blocks & Headings using PyMuPDF blocks
                blocks = fitz_page.get_text("blocks")
                for block in blocks:
                    bx0, by0, bx1, by1, btext, bno, btype = block
                    btext_clean = btext.strip()
                    if not btext_clean:
                        continue

                    # Check if block overlaps with an extracted table bbox
                    in_table = False
                    for tbox in table_bboxes:
                        if bx0 >= tbox[0] - 5 and by0 >= tbox[1] - 5 and bx1 <= tbox[2] + 5 and by1 <= tbox[3] + 5:
                            in_table = True
                            break
                    if in_table:
                        continue

                    # Detect headings based on line length or capital/bold structure
                    lines = [l.strip() for l in btext_clean.split("\n") if l.strip()]
                    if lines and (len(lines[0]) < 60 and (lines[0].isupper() or lines[0].startswith("Chapter") or lines[0].startswith("Section") or len(lines) == 1)):
                        element_type = ElementType.HEADING
                        current_section = lines[0]
                    else:
                        element_type = ElementType.TEXT

                    txt_elem = DocumentElement(
                        element_id=f"{document_id}_p{page_num}_blk{bno}",
                        element_type=element_type,
                        page_number=page_num,
                        section_title=current_section,
                        content_text=btext_clean,
                        bbox=BoundingBox(x0=bx0, y0=by0, x1=bx1, y1=by1)
                    )
                    page_elements.append(txt_elem)
                    total_elements += 1

                # 3. Extract Images & Diagrams
                image_list = fitz_page.get_images(full=True)
                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = fitz_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    img_filename = f"{document_id}_p{page_num}_img{img_idx}.{image_ext}"
                    img_path = os.path.join(settings.EXTRACTED_IMAGES_DIR, img_filename)

                    with open(img_path, "wb") as f_img:
                        f_img.write(image_bytes)

                    # Vision Analysis for Diagram Understanding
                    vision_result = vision_analyzer.analyze_image(
                        image_path=img_path,
                        context_caption=f"Image on page {page_num} of {file_name} under section {current_section}"
                    )

                    diag_text = (
                        f"[Diagram/Image: {vision_result.get('diagram_type', 'technical_diagram')}]\n"
                        f"Description: {vision_result.get('description', '')}\n"
                    )
                    if vision_result.get("components"):
                        diag_text += f"Components: {', '.join(vision_result['components'])}\n"
                    if vision_result.get("connections"):
                        diag_text += f"Connections: {', '.join(vision_result['connections'])}\n"

                    img_elem = DocumentElement(
                        element_id=f"{document_id}_p{page_num}_img{img_idx}",
                        element_type=ElementType.DIAGRAM if vision_result.get("diagram_type") != "general_image" else ElementType.IMAGE,
                        page_number=page_num,
                        section_title=current_section,
                        content_text=diag_text.strip(),
                        structured_data=vision_result,
                        image_path=img_path
                    )
                    page_elements.append(img_elem)
                    total_elements += 1

                # Full page text
                full_ptext = fitz_page.get_text("text")
                doc_pages.append(Page(
                    page_number=page_num,
                    elements=page_elements,
                    page_text=full_ptext
                ))

        fitz_doc.close()

        doc = Document(
            document_id=document_id,
            file_name=file_name,
            file_id=file_id,
            mime_type="application/pdf",
            gdrive_url=gdrive_url,
            pages=doc_pages,
            metadata={
                "pages_count": len(doc_pages),
                "elements_count": total_elements
            }
        )
        logger.info(f"Successfully parsed PDF {file_name}: {len(doc_pages)} pages, {total_elements} elements.")
        return doc
