# chunking

`backend/app/ingestion/chunking/` — turns a parsed document's flat block list into sized, section-aware chunks ready for embedding. This is step two of the pipeline: it takes parsing's output as its only input and doesn't touch embeddings or search itself. Two distinct steps live here: `chunk_document()` produces the chunks, and a separate function, `replace_document_chunks()`, persists them to `document_chunks`.

## The process, end to end

1. **Group blocks by section.** Walk `parsed.blocks` in original order and split them into runs wherever `section_path` changes. A run never gets recombined with another later in the document.
2. **Handle tables immediately.** Any table block becomes its own chunk on the spot — never merged with surrounding text, never split, even if it's larger than the target size.
3. **Split oversized text blocks.** A single block bigger than the max size gets broken on its own paragraph breaks first, falling back to sentence splitting only if one paragraph alone is still too big.
4. **Pack text blocks greedily.** Within a run, blocks accumulate into a chunk until the running total reaches the target size (default 512 tokens) — that's the common stopping point. If a single next block would push the total past the hard max (default 800 tokens) before the target is reached, the chunk closes there instead. A long section naturally becomes several chunks this way.
5. **Prepend the section breadcrumb.** Every chunk's final text is `"{section_path}\n\n{content}"`, so the section a chunk came from is baked into what gets embedded and searched — except for pre-heading content (`section_path == ""`), which is left as-is with no breadcrumb line. Tables get the same prefix; they stay whole and unsplit, they just aren't exempt from the breadcrumb.
6. **Assign indexes.** Chunks get a sequential `chunk_index` across the whole document. Persistence is a separate function (`replace_document_chunks()`), not part of `chunk_document()`.

## What a chunk looks like

```json
{
  "chunk_index": 4,
  "text": "3. Methods\n\nWe collected data from...",
  "token_count": 487,
  "page_start": 3,
  "page_end": 4,
  "section_path": "3. Methods",
  "chunk_type": "text",
  "metadata": {"chunking_config_version": "v1"}
}
```

- **`text`** — the breadcrumb-prefixed content that actually gets embedded and full-text-searched.
- **`token_count`** — counted with `tiktoken`'s `cl100k_base` encoding, the same one `text-embedding-3-small` uses.
- **`page_start`/`page_end`** — the min/max across every block packed into this chunk, so a chunk spanning several blocks reports its true page range, not just its first or last block's.
- **`section_path`** — kept as its own field too (not just baked into `text`), so citation lookups don't need to parse it back out.
- **`metadata`** — currently just the chunking config version, for debugging which settings produced a chunk. Not used for automated staleness detection — re-chunking a document always replaces all of its chunks.

## Why chunks never span two sections

A chunk boundary always falls at a section change, even if that leaves a small trailing chunk. The reverse isn't true: a long section routinely becomes several chunks, all sharing the same `section_path`. This keeps every chunk's section attribution unambiguous, at the cost of some chunks being smaller than the target size.

## Why re-chunking replaces everything

There's no per-chunk staleness tracking (no content-hash/config-version column). Re-chunking a document deletes all of its existing `document_chunks` rows and inserts the fresh set in one real transaction, so a failure partway through rolls back cleanly instead of leaving the document with a mix of old and new chunks — or with zero chunks.

## Files

- **chunker.py** — `chunk_document(parsed, config)` is the public entry point (steps 1-5 above).
- **schemas.py** — `ChunkingConfig` (target/max token size, tokenizer, config version) and `Chunk` (the pre-persistence shape).
- **`app/database/chunks.py`** — `replace_document_chunks(session, document_id, chunks)`, the persistence half, kept separate so `chunk_document()` itself has no I/O and stays trivially unit-testable.
- **`app/database/engine.py`** — `get_engine()`, the plain SQLAlchemy engine factory this and the schema-constraint tests share.

## Where the output lives

Rows in the `document_chunks` table, one per chunk, keyed by `(document_id, chunk_index)`.
