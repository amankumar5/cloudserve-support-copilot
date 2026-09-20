from app.models.document import Document, Page, DocumentElement, ElementType
from app.chunking.strategy import StructureAwareChunker


def test_structure_aware_table_chunking():
    table_elem = DocumentElement(
        element_id="tbl_1",
        element_type=ElementType.TABLE,
        page_number=1,
        section_title="Revenue Section",
        content_text="| Product | Revenue | Growth |\n| --- | --- | --- |\n| Product A | $10M | 12% |"
    )

    p1 = Page(page_number=1, elements=[table_elem], page_text="")
    doc = Document(
        document_id="doc_test",
        file_name="test.pdf",
        file_id="fid_test",
        mime_type="application/pdf",
        pages=[p1]
    )

    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    assert chunks[0].metadata.element_type == ElementType.TABLE
    assert "| Product | Revenue | Growth |" in chunks[0].content
