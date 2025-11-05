from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from PyPDF2 import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "data" / "law_manifest.json"
OUTPUT_PATH = REPO_ROOT / "data" / "seed_samples.json"

ARTICLE_RE = re.compile(r"Article\s*\((\d+)\)", re.IGNORECASE)
CHAPTER_RE = re.compile(r"Chapter\s+([A-Za-z0-9]+)", re.IGNORECASE)
SECTION_RE = re.compile(r"Section\s+([A-Za-z0-9]+)", re.IGNORECASE)
PART_RE = re.compile(r"Part\s+([A-Za-z0-9]+)", re.IGNORECASE)


@dataclass(frozen=True)
class LawMeta:
    base_id: str
    pdf_rel_path: str
    instrument: Dict[str, object]
    source: Dict[str, object]
    effective_from: str
    topics: Sequence[str]
    category: str

    @property
    def pdf_path(self) -> Path:
        return (REPO_ROOT / self.pdf_rel_path).resolve()


def load_manifest(categories: Optional[Sequence[str]]) -> List[LawMeta]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
        raw_manifest = json.load(fh)

    if not isinstance(raw_manifest, list):
        raise ValueError("Manifest must be a list of law descriptors.")

    selected: List[LawMeta] = []
    allow_all = not categories
    category_filter = {c.lower() for c in categories or []}

    for entry in raw_manifest:
        entry_category = entry.get("category", "").lower()
        if not allow_all and entry_category not in category_filter:
            continue

        selected.append(
            LawMeta(
                base_id=entry["base_id"],
                pdf_rel_path=entry["pdf_rel_path"],
                instrument=entry["instrument"],
                source=entry["source"],
                effective_from=entry["effective_from"],
                topics=entry.get("topics", []),
                category=entry_category or entry["category"],
            )
        )

    if not selected:
        available = sorted({item.get("category", "") for item in raw_manifest})
        raise ValueError(
            f"No laws matched categories={categories}. Available categories: {available}"
        )

    return selected


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        content = page.extract_text() or ""
        pages.append(content)
    return "\n".join(pages)


def chunk_articles(text: str) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    part = None
    chapter = None
    section = None
    current_article = None
    current_heading = None
    buffer: List[str] = []

    def flush():
        if current_article is None:
            return
        article_text = "\n".join(buffer).strip()
        if not article_text:
            return
        locators = {
            "part": part,
            "chapter": chapter,
            "section": section,
            "article": str(current_article),
            "rule": None,
            "clause": None,
            "item": None,
        }
        path_parts = []
        if part:
            path_parts.append(part)
        if chapter:
            path_parts.append(f"Chapter {chapter}")
        if section:
            path_parts.append(f"Section {section}")
        title = f"Article {current_article}"
        if current_heading:
            title += f" – {current_heading}"
        path_parts.append(title)
        records.append(
            {
                "article": str(current_article),
                "heading": current_heading,
                "path": " > ".join(path_parts),
                "locators": locators,
                "text": article_text,
            }
        )

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if buffer:
                buffer.append("")
            continue

        part_match = PART_RE.match(line)
        if part_match:
            part = part_match.group(0).strip()
            continue

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            chapter = chapter_match.group(1).strip()
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            section = section_match.group(1).strip()
            continue

        article_match = ARTICLE_RE.match(line)
        if article_match:
            flush()
            current_article = article_match.group(1)
            remainder = line[article_match.end() :].strip()
            current_heading = remainder if remainder else None
            buffer = []
            if current_heading:
                buffer.append(current_heading)
            continue

        if current_article is not None and current_heading is None and not buffer:
            current_heading = line
            buffer.append(line)
            continue

        if current_article is not None:
            buffer.append(line)

    flush()
    return _merge_article_segments(records)


def _merge_article_segments(segments: List[Dict[str, object]]) -> List[Dict[str, object]]:
    merged: List[Dict[str, object]] = []
    index: Dict[str, int] = {}

    for segment in segments:
        article_id = segment["article"]
        if article_id in index:
            existing = merged[index[article_id]]
            existing_text = existing["text"]
            segment_text = segment["text"]
            if segment_text:
                combined = f"{existing_text}\n{segment_text}" if existing_text else segment_text
                existing["text"] = combined
            if not existing.get("heading") and segment.get("heading"):
                existing["heading"] = segment["heading"]
            continue

        index[article_id] = len(merged)
        merged.append(segment)

    return merged


def build_record(meta: LawMeta, article_chunk: Dict[str, object]) -> Dict[str, object]:
    text_content = article_chunk["text"]
    text_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
    article_id = article_chunk["article"]
    record_id = f"{meta.base_id}#art{article_id}"

    return {
        "id": record_id,
        "jurisdiction": {
            "level": "federal",
            "name": "UAE",
            "emirate": None,
            "freezone": None,
        },
        "source": meta.source,
        "instrument": meta.instrument,
        "structure": {
            "granularity": "article",
            "path": article_chunk["path"],
            "locators": article_chunk["locators"],
        },
        "text_content": text_content,
        "text_hash": f"sha256:{text_hash}",
        "primary_lang": meta.instrument.get("official_language", "English").lower().startswith(
            "ar"
        )
        and "ar"
        or "en",
        "topics": list(meta.topics),
        "state": "in_force",
        "effective": {
            "from_date": meta.effective_from,
            "to_date": None,
            "basis": "gazette_publication",
        },
        "versions": [
            {
                "version_id": "v1",
                "event": "enacted",
                "date": meta.effective_from,
                "by_instrument": None,
                "by_url": None,
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate article-level legal slices from configured PDF manifests."
    )
    parser.add_argument(
        "--category",
        action="append",
        help="Limit generation to one or more manifest categories (default: all).",
    )
    args = parser.parse_args()

    metas = load_manifest(args.category)
    all_records: List[Dict[str, object]] = []

    for meta in metas:
        pdf_path = meta.pdf_path
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        text = extract_text(pdf_path)
        chunks = chunk_articles(text)
        for chunk in chunks:
            all_records.append(build_record(meta, chunk))

    all_records.sort(key=lambda item: item["id"])

    OUTPUT_PATH.write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(all_records)} article slices for {len(metas)} laws "
        f"into {OUTPUT_PATH.relative_to(REPO_ROOT)}"
    )


if __name__ == "__main__":
    main()
