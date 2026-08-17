# parsing

`backend/app/ingestion/parsing/` — turns a PDF into a structured JSON file describing its content, page by page and section by section. This is step one of the pipeline: nothing here does chunking, embedding, or search — it just turns a messy PDF into clean, labeled data that later steps can work with.

## The process, end to end

1. **Hash the PDF.** We SHA256 the raw file bytes to get a `content_hash`. This is the PDF's fingerprint — same bytes always produce the same hash.
2. **Check the cache.** If we've already parsed a PDF with this exact hash before, we load the saved JSON and stop here. No re-parsing.
3. **Parse with Docling.** If not cached, the PDF is handed to [Docling](https://github.com/docling-project/docling) (`DocumentConverter`), a library that reads the PDF's layout and figures out what's a heading, a paragraph, a table, a picture, etc. — the kind of understanding you'd get from looking at the page, not just extracting raw text.
4. **Normalize.** Docling's own output is detailed but awkward to use directly. We walk through it and reshape it into a flat list of simple "blocks" (see below).
5. **Cache the result.** The normalized result is saved to disk as JSON, keyed by that content hash, so next time it's instant.

## What's in the output JSON

Each parsed PDF becomes one JSON file with three things:

- **`markdown`** — the entire document as one big markdown string (Docling's full export). Useful as a quick human-readable dump of the whole paper.
- **`page_count`** — how many pages the PDF had.
- **`blocks`** — the real payload: a flat, ordered list of chunks describing the document's content. Each block looks like:
  ```json
  {
    "text": "Clinical decision-making is inherently difficult...",
    "block_type": "text",
    "page_start": 1,
    "page_end": 2,
    "section_path": "1. Introduction"
  }
  ```
  - **`text`** — the actual content (a merged paragraph of prose, or a table rendered as markdown).
  - **`block_type`** — either `"text"` or `"table"`.
  - **`page_start` / `page_end`** — which page(s) this block came from (a block can span a page break).
  - **`section_path`** — a breadcrumb of the heading(s) this block sits under, e.g. `"1. Introduction"` or `"Abstract"`. This is what lets us later say "this came from Section 3.2" instead of just "page 7."

A typical paper (~40 pages) normalizes down to roughly 80-100 blocks.

## How a block's boundaries are decided

A block is neither "one paragraph" nor "one section" — it's every consecutive run of text between two *flush points*. `normalize()` walks Docling's flat item stream in order and keeps an in-progress buffer of text, appending each `TextItem`'s text to it as it goes. That buffer gets flushed into a finished `Block` whenever one of three things happens:

1. A new heading (`SectionHeaderItem`) is reached.
2. A table (`TableItem`) is reached.
3. The document ends.

So if a section has three paragraphs before the next heading or table, all three become *one* text block — join with `"\n\n"` between each original paragraph, mirroring how they'd render in markdown. If a heading is immediately followed by another heading or a table, the empty buffer flushes nothing. A table always flushes whatever text came before it first, then becomes its own single-item block — text and tables never share a block.

`page_start`/`page_end` on a text block are the min/max page across every `TextItem` folded into it (not just the first or last), so a block that runs across a page break correctly reports both pages.

`section_path` is rebuilt from a `heading_stack` dict keyed by heading level (1, 2, 3, ...). Hitting a new heading drops any deeper levels already on the stack and sets its own level's text; the path is then every remaining level's text joined with `" > "`, in level order — which is how nested breadcrumbs like `"3. Methods > 3.2 Data Collection"` come about.

## Why "normalize" instead of using Docling's output directly

Docling's native output is a tree of many different item types (text items, section headers, tables, pictures, captions...) with their own nesting and cross-references. That's rich but painful for downstream code (chunking, embedding, citation lookup) to consume. Normalizing collapses that tree into one flat list of blocks with a consistent shape, and makes a few opinionated calls along the way:
- **Consecutive paragraphs are merged** into a single text block instead of staying as separate sentence/paragraph fragments — better chunk boundaries later. (See "How a block's boundaries are decided" above for the exact rule.)
- **Tables are kept whole** and exported as markdown (not merged with surrounding text), since splitting a table mid-row would destroy it.
- **Section headings aren't emitted as their own blocks** — instead, every block below a heading carries that heading in `section_path`, so you always know "where" a block is without a separate lookup.
- **Pictures and table captions are dropped** — captions get folded in as part of the table's own export; standalone images aren't retained as content since we're only sourcing text/tables for now.

## Why the cache exists

Docling parsing is slow (it's doing real layout analysis, not just text extraction) and the underlying model is deterministic for the same input file. Since the cache key is a hash of the file's bytes, "same PDF → instant reload" and "different/edited PDF → re-parsed automatically" both fall out for free, with no manual invalidation needed.

## Files

- **parser.py** (`app/ingestion/parsing/`) — `parse_pdf(pdf_path, cache_dir)` is the public entry point (steps 1-5 above). `normalize(doc)` does the Docling-tree-to-blocks walk.
- **cache.py** (`app/ingestion/parsing/`) — `hash_file`, `load_cached`, `write_cache`. Writes go through a `.tmp` file + atomic rename so a crash mid-write can't leave a corrupt cache entry.
- **schemas.py** (`app/ingestion/parsing/`) — the Pydantic models that define the JSON shape: `ChunkType` (`text`/`table`), `Block`, `ParsedDocument`.

## Where the output lives

Parsed JSON files land in `data/papers/parsed/`, named `<content_hash>.json`.
