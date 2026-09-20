import os
import pytest
from app.parsing.docx_parser import DOCXParser
from app.models.document import ElementType


def test_docx_parser():
    sample_path = "data/sample_docs/DOC-AUTH-001_resolving_invalid_credential_e.docx"
    if not os.path.exists(sample_path):
        pytest.skip("Sample docx file not found.")

    parser = DOCXParser()
    doc = parser.parse(file_path=sample_path, file_id="doc_auth_1", file_name="DOC-AUTH-001.docx")

    assert doc.file_name == "DOC-AUTH-001.docx"
    assert len(doc.pages) == 1
    assert len(doc.pages[0].elements) > 0

    has_heading = any(e.element_type == ElementType.HEADING for e in doc.pages[0].elements)
    assert has_heading
