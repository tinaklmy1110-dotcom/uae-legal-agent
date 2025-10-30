from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable
from typing import List

from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine

from ..db import PGVECTOR_DIM, PGVECTOR_METRIC
from ..search import embed

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

OPERATOR_MAP = {
    "cosine": "<=>",
    "euclidean": "<->",
    "ip": "<#>",
}


def make_engine() -> Engine:
    db_url = os.getenv("DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    return create_engine(db_url, future=True, pool_pre_ping=True)


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


def similarity_from_measure(value: float) -> float:
    if PGVECTOR_METRIC == "cosine":
        return 1.0 - float(value)
    if PGVECTOR_METRIC == "euclidean":
        return 1.0 / (1.0 + float(value))
    # inner product (operator returns negative inner product; invert sign)
    return -float(value)


def search(args: argparse.Namespace) -> None:
    engine = make_engine()
    operator = OPERATOR_MAP.get(PGVECTOR_METRIC, "<=>")
    embedding = load_embedding(args.embedding, args.query)

    sql = text(
        f"""
        SELECT
            id,
            instrument_title,
            embedding {operator} :query_embedding AS measure
        FROM legal_slices
        WHERE embedding IS NOT NULL
        ORDER BY embedding {operator} :query_embedding
        LIMIT :limit;
        """
    )

    try:
        with engine.begin() as conn:
            rows = conn.execute(
                sql, {"query_embedding": embedding, "limit": args.top_k}
            ).all()
    except Exception as err:  # noqa: BLE001
        print(f"{RED}❌ Vector search failed: {err}{RESET}")
        sys.exit(1)

    if not rows:
        print(f"{YELLOW}⚠ No records found in legal_slices.{RESET}")
        return

    print(f"{BLUE}🔎 Top {len(rows)} results (metric={PGVECTOR_METRIC}):{RESET}")
    for rank, (slice_id, title, measure) in enumerate(rows, start=1):
        similarity = similarity_from_measure(float(measure))
        print(
            f"  {rank:02d}. {slice_id} | {title} | distance={measure:.6f} | similarity≈{similarity:.6f}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a vector similarity search over legal_slices."
    )
    parser.add_argument(
        "--query",
        help="Query text used to generate a placeholder embedding when --embedding is omitted.",
    )
    parser.add_argument(
        "--embedding",
        help="Embedding vector as JSON string or path to JSON file.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of nearest neighbours to return (default: 5).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        search(args)
    except ValueError as err:
        print(f"{RED}❌ {err}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
