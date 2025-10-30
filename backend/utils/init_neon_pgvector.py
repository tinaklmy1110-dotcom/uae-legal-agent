from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

SUPPORTED_METRICS = {
    "cosine": "vector_cosine_ops",
    "ip": "vector_ip_ops",
    "euclidean": "vector_l2_ops",
}


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable '{name}' is required.")
    return value


def make_engine() -> Engine:
    db_url = get_env("DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    return create_engine(db_url, future=True, pool_pre_ping=True)


def resolve_dim() -> int:
    raw = os.getenv("PGVECTOR_DIM", "384")
    try:
        dim = int(raw)
        if dim <= 0:
            raise ValueError
        return dim
    except ValueError as exc:
        raise RuntimeError("PGVECTOR_DIM must be a positive integer.") from exc


def resolve_metric() -> tuple[str, str]:
    metric = os.getenv("PGVECTOR_METRIC", "cosine").lower()
    if metric not in SUPPORTED_METRICS:
        print(f"{YELLOW}⚠ Unsupported PGVECTOR_METRIC '{metric}', defaulting to cosine.{RESET}")
        metric = "cosine"
    opclass = SUPPORTED_METRICS[metric]
    return metric, opclass


@contextmanager
def db_connection(engine: Engine):
    with engine.begin() as connection:
        yield connection


def run() -> None:
    dim = resolve_dim()
    metric, opclass = resolve_metric()
    engine = make_engine()

    extension_sql = text("CREATE EXTENSION IF NOT EXISTS vector;")
    table_sql = text(
        f"""
        CREATE TABLE IF NOT EXISTS legal_slices (
            id TEXT PRIMARY KEY,
            jurisdiction TEXT NOT NULL,
            instrument_title TEXT NOT NULL,
            structure_path TEXT NOT NULL,
            topics TEXT[],
            effective_from DATE NOT NULL,
            effective_to DATE,
            embedding vector({dim})
        );
        """
    )
    index_statements = [
        text("CREATE INDEX IF NOT EXISTS legal_slices_jurisdiction_idx ON legal_slices (jurisdiction);"),
        text("CREATE INDEX IF NOT EXISTS legal_slices_effective_idx ON legal_slices (effective_from, effective_to);"),
        text("CREATE INDEX IF NOT EXISTS legal_slices_topics_idx ON legal_slices USING GIN (topics);"),
        text(
            f"CREATE INDEX IF NOT EXISTS legal_slices_embedding_idx "
            f"ON legal_slices USING hnsw (embedding {opclass});"
        ),
    ]

    try:
        with db_connection(engine) as conn:
            conn.execute(extension_sql)
            conn.execute(table_sql)
            for statement in index_statements:
                conn.execute(statement)
    except Exception as err:  # noqa: BLE001
        print(f"{RED}❌ Failed to initialise pgvector schema: {err}{RESET}")
        sys.exit(1)

    print(
        f"{GREEN}✅ legal_slices ready (dim={dim}, metric={metric}, url={engine.url.render_as_string(hide_password=True)}){RESET}"
    )


if __name__ == "__main__":
    run()
