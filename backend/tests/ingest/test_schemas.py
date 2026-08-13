from app.ingest.schemas import Block, ChunkType, ParsedDocument


def test_block_round_trips_through_json():
    block = Block(
        text="Some paragraph text.",
        block_type=ChunkType.TEXT,
        page_start=3,
        page_end=3,
        section_path="Methods > Training Data",
    )
    restored = Block.model_validate_json(block.model_dump_json())
    assert restored == block


def test_table_block_type_serializes_as_plain_string():
    block = Block(
        text="| a | b |\n| - | - |",
        block_type=ChunkType.TABLE,
        page_start=6,
        page_end=6,
        section_path="Results",
    )
    assert block.model_dump()["block_type"] == "table"


def test_parsed_document_round_trips_through_json():
    doc = ParsedDocument(
        markdown="# Title\n\nBody text.",
        page_count=19,
        blocks=[
            Block(
                text="Body text.",
                block_type=ChunkType.TEXT,
                page_start=1,
                page_end=1,
                section_path="",
            )
        ],
    )
    restored = ParsedDocument.model_validate_json(doc.model_dump_json())
    assert restored == doc
