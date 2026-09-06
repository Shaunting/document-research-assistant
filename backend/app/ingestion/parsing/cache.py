import hashlib
from pathlib import Path

from app.ingestion.parsing.schemas import ParsedDocument


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cache_path(content_hash: str, cache_dir: Path) -> Path:
    return cache_dir / f"{content_hash}.json"


def load_cached(content_hash: str, cache_dir: Path) -> ParsedDocument | None:
    path = _cache_path(content_hash, cache_dir)
    if not path.exists():
        return None
    return ParsedDocument.model_validate_json(path.read_text())


def write_cache(content_hash: str, parsed: ParsedDocument, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    final_path = _cache_path(content_hash, cache_dir)
    tmp_path = final_path.with_suffix(".json.tmp")
    tmp_path.write_text(parsed.model_dump_json())
    tmp_path.replace(final_path)
