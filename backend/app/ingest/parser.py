# backend/app/ingest/parser.py
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import (
    DoclingDocument,
    PictureItem,
    SectionHeaderItem,
    TableItem,
    TextItem,
)

from app.ingest.cache import hash_file, load_cached, write_cache
from app.ingest.schemas import Block, ChunkType, ParsedDocument


def parse_pdf(pdf_path: Path, cache_dir: Path) -> ParsedDocument:
    content_hash = hash_file(pdf_path)
    cached = load_cached(content_hash, cache_dir=cache_dir)
    if cached is not None:
        return cached

    result = DocumentConverter().convert(str(pdf_path))
    parsed = normalize(result.document)
    write_cache(content_hash, parsed, cache_dir=cache_dir)
    return parsed


def normalize(doc: DoclingDocument) -> ParsedDocument:
    blocks: list[Block] = []
    heading_stack: dict[int, str] = {}
    current_text_parts: list[str] = []
    current_page_start: int | None = None
    current_page_end: int | None = None

    def section_path() -> str:
        return " > ".join(heading_stack[level] for level in sorted(heading_stack))

    def flush_text_block() -> None:
        nonlocal current_text_parts, current_page_start, current_page_end
        if current_text_parts:
            blocks.append(
                Block(
                    text="\n\n".join(current_text_parts),
                    block_type=ChunkType.TEXT,
                    page_start=current_page_start,
                    page_end=current_page_end,
                    section_path=section_path(),
                )
            )
        current_text_parts = []
        current_page_start = None
        current_page_end = None

    for item, _tree_level in doc.iterate_items(traverse_pictures=True):
        if isinstance(item, SectionHeaderItem):
            flush_text_block()
            heading_stack = {
                level: text for level, text in heading_stack.items() if level < item.level
            }
            heading_stack[item.level] = item.text
            continue

        if isinstance(item, TableItem):
            flush_text_block()
            page_start, page_end = _page_range(item)
            blocks.append(
                Block(
                    text=item.export_to_markdown(doc),
                    block_type=ChunkType.TABLE,
                    page_start=page_start,
                    page_end=page_end,
                    section_path=section_path(),
                )
            )
            continue

        if isinstance(item, PictureItem):
            caption = _resolve_caption_text(item, doc)
            if caption:
                current_text_parts.append(caption)
                page_start, page_end = _page_range(item)
                current_page_start = min(filter(None, [current_page_start, page_start]))
                current_page_end = max(filter(None, [current_page_end, page_end]))
            continue

        if isinstance(item, TextItem):
            page_start, page_end = _page_range(item)
            current_text_parts.append(item.text)
            current_page_start = (
                page_start if current_page_start is None else min(current_page_start, page_start)
            )
            current_page_end = (
                page_end if current_page_end is None else max(current_page_end, page_end)
            )

    flush_text_block()

    return ParsedDocument(
        markdown=doc.export_to_markdown(),
        page_count=len(doc.pages),
        blocks=blocks,
    )


def _page_range(item) -> tuple[int, int]:
    pages = [p.page_no for p in item.prov]
    return min(pages), max(pages)


def _resolve_caption_text(item, doc: DoclingDocument) -> str | None:
    if not item.captions:
        return None
    return item.captions[0].resolve(doc).text
