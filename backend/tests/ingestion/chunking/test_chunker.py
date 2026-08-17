import pytest

from app.ingestion.chunking.chunker import _count_tokens, _group_by_section, chunk_document
from app.ingestion.chunking.schemas import ChunkingConfig
from app.ingestion.parsing.schemas import Block, ChunkType, ParsedDocument


def _text_block(text: str, section_path: str = "Intro", page: int = 1) -> Block:
    return Block(
        text=text,
        block_type=ChunkType.TEXT,
        page_start=page,
        page_end=page,
        section_path=section_path,
    )


def _table_block(text: str, section_path: str = "Results", page: int = 1) -> Block:
    return Block(
        text=text,
        block_type=ChunkType.TABLE,
        page_start=page,
        page_end=page,
        section_path=section_path,
    )


def test_count_tokens_matches_cl100k_base():
    config = ChunkingConfig()
    assert _count_tokens("hello world", config) == 2


def test_group_by_section_splits_on_section_change():
    blocks = [
        _text_block("a", section_path="Abstract"),
        _text_block("b", section_path="Abstract"),
        _text_block("c", section_path="Methods"),
    ]
    runs = _group_by_section(blocks)
    assert len(runs) == 2
    assert [b.text for b in runs[0]] == ["a", "b"]
    assert [b.text for b in runs[1]] == ["c"]


def test_group_by_section_treats_empty_string_as_its_own_run():
    blocks = [
        _text_block("preamble", section_path=""),
        _text_block("a", section_path="Abstract"),
    ]
    runs = _group_by_section(blocks)
    assert len(runs) == 2
    assert runs[0][0].section_path == ""


def test_table_block_becomes_its_own_chunk():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[_table_block("| a | b |\n| - | - |", section_path="Results", page=4)],
    )
    chunks = chunk_document(parsed)
    assert len(chunks) == 1
    assert chunks[0].chunk_type == ChunkType.TABLE
    assert chunks[0].page_start == 4
    assert chunks[0].page_end == 4


def test_table_never_merges_with_surrounding_text():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("before", section_path="Results", page=4),
            _table_block("| a | b |", section_path="Results", page=4),
            _text_block("after", section_path="Results", page=4),
        ],
    )
    chunks = chunk_document(parsed)
    types = [c.chunk_type for c in chunks]
    assert ChunkType.TABLE in types
    table_chunk = next(c for c in chunks if c.chunk_type == ChunkType.TABLE)
    assert "before" not in table_chunk.text
    assert "after" not in table_chunk.text


def test_small_text_blocks_in_same_section_pack_into_one_chunk():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("one.", section_path="Abstract", page=1),
            _text_block("two.", section_path="Abstract", page=1),
        ],
    )
    chunks = chunk_document(parsed)
    assert len(chunks) == 1
    assert "one." in chunks[0].text
    assert "two." in chunks[0].text


def test_chunk_never_spans_two_sections():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("abstract text", section_path="Abstract", page=1),
            _text_block("intro text", section_path="Introduction", page=1),
        ],
    )
    chunks = chunk_document(parsed)
    sections = {c.section_path for c in chunks}
    assert sections == {"Abstract", "Introduction"}
    assert len(chunks) == 2


def test_long_section_packs_into_multiple_chunks():
    config = ChunkingConfig(target_tokens=5, max_tokens=8)
    # NOTE: fixture calibrated against the real cl100k_base tokenizer (not the
    # brief's original "word{i} " * 6, which already tokenizes to 13 tokens per
    # block -- above max_tokens on its own). A single "word{i} " repeat is 3
    # tokens (comfortably under target_tokens=5), so pairs of blocks accumulate
    # before a group is pushed, and the joined+breadcrumbed chunk text lands at
    # exactly 8 tokens (<= max_tokens=8), giving 2 packed chunks from 4 blocks.
    blocks = [_text_block(f"word{i} ", section_path="Methods", page=1) for i in range(4)]
    parsed = ParsedDocument(markdown="", page_count=1, blocks=blocks)
    chunks = chunk_document(parsed, config)
    assert len(chunks) > 1
    assert all(c.section_path == "Methods" for c in chunks)
    for c in chunks:
        assert c.token_count <= config.max_tokens


def test_oversized_block_splits_on_paragraph_boundary():
    config = ChunkingConfig(target_tokens=10, max_tokens=15)
    # NOTE: fixture calibrated against the real tokenizer -- the brief's
    # original "* 10" repeat makes each paragraph 20 tokens on its own,
    # already over max_tokens=15, which would force a sentence-level
    # fallback split instead of the clean paragraph-boundary split this
    # test wants to exercise. "* 4" gives each paragraph 8 tokens (10 with
    # the section breadcrumb), comfortably under max_tokens, while the
    # combined block (17 tokens) still exceeds max_tokens and triggers the
    # split.
    long_block = _text_block(
        ("first paragraph " * 4).strip() + "\n\n" + ("second paragraph " * 4).strip(),
        section_path="Methods",
    )
    parsed = ParsedDocument(markdown="", page_count=1, blocks=[long_block])
    chunks = chunk_document(parsed, config)
    assert len(chunks) == 2
    for c in chunks:
        assert c.token_count <= config.max_tokens


def test_paragraph_still_oversized_after_split_falls_back_to_sentences():
    config = ChunkingConfig(target_tokens=10, max_tokens=15)
    short_paragraph = "Short one."
    long_paragraph = "This is a sentence. " * 10 + "Final sentence here."
    long_block = _text_block(
        short_paragraph + "\n\n" + long_paragraph, section_path="Methods"
    )
    parsed = ParsedDocument(markdown="", page_count=1, blocks=[long_block])
    chunks = chunk_document(parsed, config)
    assert len(chunks) >= 3  # short paragraph + at least 2 sentence-split pieces
    for c in chunks:
        assert c.token_count <= config.max_tokens
    all_text = " ".join(c.text for c in chunks)
    assert "Short one." in all_text
    assert "Final sentence here." in all_text


def test_chunk_document_raises_on_empty_blocks():
    parsed = ParsedDocument(markdown="", page_count=1, blocks=[])
    with pytest.raises(ValueError):
        chunk_document(parsed)


def test_breadcrumb_is_prepended_when_section_path_present():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[_text_block("body text", section_path="Methods", page=1)],
    )
    chunks = chunk_document(parsed)
    assert chunks[0].text == "Methods\n\nbody text"


def test_no_breadcrumb_line_when_section_path_is_empty():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[_text_block("preamble text", section_path="", page=1)],
    )
    chunks = chunk_document(parsed)
    assert chunks[0].text == "preamble text"


def test_chunk_index_is_sequential_across_whole_document():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("a", section_path="Abstract", page=1),
            _text_block("b", section_path="Introduction", page=1),
            _table_block("| x |", section_path="Introduction", page=1),
        ],
    )
    chunks = chunk_document(parsed)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunk_page_range_is_min_max_across_packed_blocks():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("a", section_path="Methods", page=3),
            _text_block("b", section_path="Methods", page=4),
        ],
    )
    chunks = chunk_document(parsed)
    assert len(chunks) == 1
    assert chunks[0].page_start == 3
    assert chunks[0].page_end == 4


def test_breadcrumb_tokens_are_budgeted_into_max_tokens():
    # Regression test: a long section_path breadcrumb (prepended only in
    # _blocks_to_chunk, after packing/splitting decisions) must not be able
    # to push a chunk's final token_count over config.max_tokens. This
    # reproduces the reviewer's repro: a single text block whose raw token
    # count (59) is under max_tokens=60 -- so, without breadcrumb budgeting,
    # _split_oversized_block leaves it untouched and the resulting chunk's
    # token_count (raw block + 17-token breadcrumb) comes out to 76, over
    # the 60-token cap.
    config = ChunkingConfig(target_tokens=50, max_tokens=60)
    section_path = "Chapter 4: Experimental Results and Ablation Studies on Model Robustness"
    sentence = "The model shows strong robustness across diverse evaluation settings."
    body = " ".join([sentence] * 5) + " Final check here."
    long_block = _text_block(body, section_path=section_path)
    parsed = ParsedDocument(markdown="", page_count=1, blocks=[long_block])

    chunks = chunk_document(parsed, config)

    assert len(chunks) > 1
    for c in chunks:
        assert c.token_count <= config.max_tokens
    all_text = " ".join(c.text for c in chunks)
    assert "Final check here." in all_text
