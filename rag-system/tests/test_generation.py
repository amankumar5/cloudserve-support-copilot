from app.models.chunk import Chunk, ChunkMetadata, ElementType
from app.generation.generator import GroundedGenerator


def test_grounded_generator_empty_context():
    gen = GroundedGenerator()
    resp = gen.generate_answer(question="What is the revenue?", retrieved_chunks=[])
    assert "not contain enough information" in resp.answer
    assert len(resp.sources) == 0


def test_grounded_generator_citations():
    gen = GroundedGenerator()
    c_meta = ChunkMetadata(
        chunk_id="chk_1",
        document_id="doc_1",
        file_id="f1",
        file_name="report.pdf",
        page_number=3,
        section="Financials",
        element_type=ElementType.TABLE
    )
    chunk = Chunk(chunk_id="chk_1", content="Product A revenue is $10M", metadata=c_meta)

    resp = gen.generate_answer(question="What is Product A revenue?", retrieved_chunks=[(chunk, 0.95)])
    assert len(resp.sources) == 1
    assert resp.sources[0].document_name == "report.pdf"
    assert resp.sources[0].page_number == 3
