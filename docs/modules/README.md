# Modules

Quick "what's in here" notes per code module, written so someone who doesn't want to read the code can understand what it does and why. Not a spec, not a plan — just enough to jog memory or onboard fast.

## Index

- [parsing.md](parsing.md) — `backend/app/ingestion/parsing/`, PDF parsing into page-aware blocks
- [chunking.md](chunking.md) — `backend/app/ingestion/chunking/`, blocks into sized, section-aware chunks

## How to write one of these

Lead with **the process**, not the file list. The wrong way to structure this doc is "here's file A, here's file B, here's file C" — that tells you where things are but not what actually happens. The right way is to explain the thing like you're describing it to a teammate at a whiteboard, then let the file list be a reference at the bottom for whoever wants to go read code next.

A good module doc covers, roughly in this order:

1. **One-line summary** — what this module is for and where it lives (path).
2. **The process, end to end** — numbered steps of what happens from input to output. Someone non-technical should be able to follow the flow.
3. **The data** — if the module produces or consumes a specific data shape (JSON, a DB row, an API payload...), show a real example, not just a schema. Explain what each field means and why it exists.
4. **Why, not just what** — for any non-obvious design choice (a cache, a normalization step, a specific ordering, a merge rule), explain the reasoning. "Why does this exist" and "why does it work this way" are the things code alone doesn't tell you.
5. **Files** — a short reference list of files/functions and their one-line role, for when someone needs to go find the actual code. This is supporting material, not the spine of the doc.
6. **Where output lives**, if relevant (e.g. a directory on disk, a table name).

Other guidelines:
- Use a real example pulled from actual data/output where possible, not a hypothetical one — it's more trustworthy and more concrete.
- Keep it brief. If a section would just restate the code line-by-line, cut it — this doc is for the "why/what", not a code walkthrough.
- One file per module, named after the module (e.g. `ingest.md` for `app/ingest/`). Add an index line above when you add one.
- When a module changes meaningfully, update its doc in the same pass — stale docs are worse than no docs.

[ingest.md](ingest.md) is the reference example to follow.
