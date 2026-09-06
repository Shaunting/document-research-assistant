from app.ingestion.chunking.schemas import Chunk, ChunkingConfig
from app.ingestion.parsing.schemas import ChunkType


def test_chunking_config_defaults():
    config = ChunkingConfig()
    assert config.version == "v1"
    assert config.target_tokens == 512
    assert config.max_tokens == 800
    assert config.tokenizer == "cl100k_base"


def test_chunk_round_trips_through_json():
    chunk = Chunk(
        chunk_index=0,
        text="Methods\n\nSome paragraph text.",
        token_count=5,
        page_start=3,
        page_end=3,
        section_path="Methods",
        chunk_type=ChunkType.TEXT,
        metadata={"chunking_config_version": "v1"},
    )
    restored = Chunk.model_validate_json(chunk.model_dump_json())
    assert restored == chunk


def test_chunk_metadata_defaults_to_none():
    chunk = Chunk(
        chunk_index=0,
        text="body",
        token_count=1,
        page_start=1,
        page_end=1,
        section_path="",
        chunk_type=ChunkType.TABLE,
    )
    assert chunk.metadata is None
