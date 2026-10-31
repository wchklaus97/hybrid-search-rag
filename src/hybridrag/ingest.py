"""Stage 1 - Ingest: read files into Documents, keeping provenance and org metadata.

Folder layout is the org chart: <entity>/<department>/<file>  ->  entity, department.
Several root folders can be indexed together (e.g. the corpus plus distractor documents).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

from pypdf import PdfReader

TEXT_SUFFIXES = {".md", ".markdown", ".txt"}


@dataclass(frozen=True)
class Document:
    source: str  # path relative to its root folder
    page: int | None  # 1-based page for PDFs, None for text files
    text: str
    entity: str = ""
    department: str = ""
    period: str = ""  # e.g. "2025-26": the first fiscal or data-year range in the opening text


_PERIOD = re.compile(r"(20\d{2})\s*[-/–]\s*(20\d{2}|\d{2})")


def extract_period(text: str) -> str:
    """First year range in the opening 2000 characters, normalised: 2025/26 and 2025-2026 -> 2025-26."""
    m = _PERIOD.search(text[:2000])
    if not m:
        return ""
    start, end = m.group(1), m.group(2)
    return f"{start}-{end[-2:]}" if int(end[-2:]) == (int(start) + 1) % 100 else ""


def org_metadata(rel_path: str) -> tuple[str, str]:
    parts = rel_path.split("/")
    if len(parts) >= 3:
        return parts[0], parts[1]
    return ("", parts[0]) if len(parts) == 2 else ("", "")


def load_documents(folder: str | Path) -> list[Document]:
    root = Path(folder)
    if not root.is_dir():
        raise FileNotFoundError(f"Not a folder: {root}")
    docs: list[Document] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        entity, dept = org_metadata(rel)
        suffix = path.suffix.lower()
        if suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            docs.append(Document(rel, None, text, entity, dept, extract_period(text)))
        elif suffix == ".pdf":
            for n, page in enumerate(PdfReader(path).pages, start=1):
                if text := (page.extract_text() or "").strip():
                    docs.append(Document(rel, n, text, entity, dept, extract_period(text)))
    return docs
