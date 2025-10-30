from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable
from datetime import date
from typing import List

from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine

from ..db import PGVECTOR_DIM
from ..search import embed

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def make_engine() -> Engine:
    db_url = os.getenv("DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    return create_engine(db_url, future=True, pool_pre_ping=True)


def parse_topics(value: str | None) -> List[str]:
    if not value:
        return []
    return [topic.strip() for topic in value.split(",") if topic.strip()]


def parse_date(value: str | None, fallback: date | None = None) -> date | None:
    if value in (None, ""):
        return fallback
    return date.fromisoformat(value)


def load_embedding(arg: str | None, text_hint: str | None) -> List[float]:
    if arg:
        if os.path.isfile(arg):
            with open(arg, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        else:
            data = json.loads(arg)

        if not isinstance(data, Iterable):
            raise ValueError("Embedding must be a sequence of numbers.")
        vector = [float(x) for x in data]
    else:
        basis = text_hint or "uae-legal-agent"
        vector = embed(basis).tolist()

    if len(vector) != PGVECTOR_DIM:
        raise ValueError(
            f"Embedding length {len(vector)} does not match PGVECTOR_DIM={PGVECTOR_DIM}."
        )
    return vector


def upsert_record(args: argparse.Namespace) -> None:
    engine = make_engine()
    topics = parse_topics(args.topics)
    effective_from = parse_date(args.effective_from, fallback=date.today())
    effective_to = parse_date(args.effective_to)
    embedding = load_embedding(args.embedding, args.text)

    sql = text(
        """
        INSERT INTO legal_slices (
            id,
            jurisdiction,
            instrument_title,
            structure_path,
            topics,
            effective_from,
            effective_to,
            embedding
        ) VALUES (
            :id,
            :jurisdiction,
            :instrument_title,
            :structure_path,
            :topics,
            :effective_from,
            :effective_to,
            :embedding
        )
        ON CONFLICT (id) DO UPDATE SET
            jurisdiction = EXCLUDED.jurisdiction,
            instrument_title = EXCLUDED.instrument_title,
            structure_path = EXCLUDED.structure_path,
            topics = EXCLUDED.topics,
            effective_from = EXCLUDED.effective_from,
            effective_to = EXCLUDED.effective_to,
            embedding = EXCLUDED.embedding;
        """
    )

    payload = {
        "id": args.id,
        "jurisdiction": args.jurisdiction,
        "instrument_title": args.instrument_title,
        "structure_path": args.structure_path,
        "topics": topics or None,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "embedding": embedding,
    }

    try:
        with engine.begin() as conn:
            conn.execute(sql, payload)
    except Exception as err:  # noqa: BLE001
        print(f"{RED}❌ Failed to upsert slice '{args.id}': {err}{RESET}")
        sys.exit(1)

    print(
        f"{GREEN}✅ Upserted slice '{args.id}' ({args.instrument_title}) into legal_slices.{RESET}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Insert or update a legal slice record (with embedding) in legal_slices."
    )
    parser.add_argument("--id", required=True, help="Primary identifier for the slice.")
    parser.add_argument("--jurisdiction", required=True, help="Jurisdiction label.")
    parser.add_argument(
        "--instrument-title", required=True, help="Instrument or law title."
    )
    parser.add_argument(
        "--structure-path", required=True, help="Structure path (e.g., 'Chapter > Article')."
    )
    parser.add_argument(
        "--topics",
        help="Comma-separated list of topics (e.g., tenancy,real_estate).",
    )
    parser.add_argument(
        "--effective-from",
        help="Effective from date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--effective-to",
        help="Effective to date (YYYY-MM-DD). Optional.",
    )
    parser.add_argument(
        "--embedding",
        help="Embedding vector as JSON string or path to JSON file. Defaults to deterministic placeholder from --text.",
    )
    parser.add_argument(
        "--text",
        help="Text used to derive deterministic placeholder embedding when --embedding is omitted.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    upsert_record(args)


if __name__ == "__main__":
    main()
