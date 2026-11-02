from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .models import Evidence


@dataclass(frozen=True)
class GuidelineDocument:
    document_id: str
    filename: str
    title: str
    version: str
    scope: tuple[str, ...]


DOCUMENTS = (
    GuidelineDocument("ATA_DTC_2025", "ringel-et-al-2025-2025-american-thyroid-association-management-guidelines-for-adult-patients-with-differentiated.pdf", "ATA 2025 differentiated thyroid cancer guideline", "2025", ("differentiated",)),
    GuidelineDocument("ATA_DTC_EXEC_2025", "praw-et-al-2025-executive-summary-of-the-2025-american-thyroid-association-management-guidelines-for-adult-patients.pdf", "ATA 2025 differentiated thyroid cancer executive summary", "2025", ("differentiated",)),
    GuidelineDocument("ATA_ATC_2021", "bible-et-al-2021-2021-american-thyroid-association-guidelines-for-management-of-patients-with-anaplastic-thyroid-cancer.pdf", "ATA 2021 anaplastic thyroid cancer guideline", "2021", ("anaplastic",)),
    GuidelineDocument("ASCO_SYSTEMIC_2026", "saba-et-al-2026-systemic-treatment-of-thyroid-cancer-asco-guideline.pdf", "ASCO systemic treatment of thyroid cancer guideline", "2026", ("differentiated", "anaplastic", "medullary", "poorly_differentiated")),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunks(text: str, *, size: int = 1200) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > size and current:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def build_index(source_dir: Path, output_path: Path) -> dict:
    records: list[dict] = []
    manifest: list[dict] = []
    for document in DOCUMENTS:
        path = source_dir / document.filename
        if not path.exists():
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        reader = PdfReader(str(path))
        extracted = 0
        for page_number, page in enumerate(reader.pages, start=1):
            text = _normalize(page.extract_text() or "")
            if not text:
                continue
            extracted += 1
            for index, chunk in enumerate(_chunks(text), start=1):
                records.append({
                    "chunk_id": f"{document.document_id}:p{page_number}:c{index}",
                    "document_id": document.document_id,
                    "title": document.title,
                    "version": document.version,
                    "scope": list(document.scope),
                    "page": page_number,
                    "text": chunk,
                    "sha256": digest,
                })
        if not extracted:
            raise ValueError(f"Nenhum texto extraível em {path.name}")
        manifest.append({"document_id": document.document_id, "filename": document.filename, "title": document.title, "version": document.version, "scope": list(document.scope), "sha256": digest})
    payload = {"schema_version": "1", "documents": manifest, "chunks": records}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


class GuidelineRetriever:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path
        self._index = json.loads(index_path.read_text()) if index_path.exists() else {"schema_version": "1", "documents": [], "chunks": []}

    @property
    def version(self) -> str:
        return "+".join(f"{item['document_id']}:{item['version']}" for item in self._index["documents"]) or "unavailable"

    def retrieve(self, query: str, *, scope: str | None = None, limit: int = 3) -> list[Evidence]:
        terms = {token.casefold() for token in re.findall(r"[\w-]{3,}", query)}
        scored: list[tuple[int, dict]] = []
        for chunk in self._index["chunks"]:
            if scope and scope not in chunk["scope"]:
                continue
            score = sum(term in chunk["text"].casefold() for term in terms)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1]["chunk_id"]))
        return [Evidence(
            finding=item["text"],
            source=f"{item['document_id']}:{item['version']}:p{item['page']}:{item['chunk_id']}",
            document_id=item["document_id"],
            guideline_version=item["version"],
            page=item["page"],
            chunk_id=item["chunk_id"],
            scope=item["scope"],
            relevance=f"{score} termos da consulta correspondem ao trecho.",
        ) for score, item in scored[:limit]]
