from __future__ import annotations

import os
import warnings
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


load_dotenv()

DEFAULT_DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST") or "db"
DEFAULT_DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DEFAULT_DB_NAME = os.getenv("POSTGRES_DB", "uae_legal")
DEFAULT_DB_USER = os.getenv("POSTGRES_USER", "postgres")
DEFAULT_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DEFAULT_DB_URL = (
    f"postgresql+psycopg://{DEFAULT_DB_USER}:{DEFAULT_DB_PASSWORD}"
    f"@{DEFAULT_DB_HOST}:{DEFAULT_DB_PORT}/{DEFAULT_DB_NAME}"
)
SUPPORTED_METRICS = {
    "cosine": "vector_cosine_ops",
    "ip": "vector_ip_ops",
    "euclidean": "vector_l2_ops",
}

DB_URL = os.getenv("DB_URL", DEFAULT_DB_URL)

try:
    PGVECTOR_DIM = int(os.getenv("PGVECTOR_DIM", "384"))
except ValueError:
    warnings.warn("Invalid PGVECTOR_DIM provided; falling back to 384.")
    PGVECTOR_DIM = 384

PGVECTOR_METRIC = os.getenv("PGVECTOR_METRIC", "cosine").lower()
if PGVECTOR_METRIC not in SUPPORTED_METRICS:
    warnings.warn(
        f"Unsupported PGVECTOR_METRIC '{PGVECTOR_METRIC}', defaulting to 'cosine'."
    )
    PGVECTOR_METRIC = "cosine"

engine = create_engine(DB_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

DATABASE_DDL = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS legal_slice (
  id TEXT PRIMARY KEY,
  level TEXT NOT NULL,
  name TEXT NOT NULL,
  emirate TEXT,
  freezone TEXT,
  portal TEXT NOT NULL,
  url TEXT NOT NULL,
  gazette TEXT,
  type TEXT NOT NULL,
  number TEXT NOT NULL,
  year INT NOT NULL,
  title TEXT NOT NULL,
  issuer TEXT,
  official_language TEXT NOT NULL,
  granularity TEXT NOT NULL,
  path TEXT NOT NULL,
  part TEXT,
  chapter TEXT,
  section TEXT,
  article TEXT,
  rule TEXT,
  clause TEXT,
  item TEXT,
  text_content TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  primary_lang TEXT NOT NULL,
  topics TEXT[],
  state TEXT NOT NULL,
  effective_from DATE NOT NULL,
  effective_to DATE,
  vector_embedding vector({PGVECTOR_DIM})
);

CREATE INDEX IF NOT EXISTS idx_jurisdiction ON legal_slice(level, name, emirate, freezone);
CREATE INDEX IF NOT EXISTS idx_state ON legal_slice(state);
CREATE INDEX IF NOT EXISTS idx_topics ON legal_slice USING GIN (topics);
CREATE INDEX IF NOT EXISTS idx_effective ON legal_slice (effective_from, effective_to);
"""


def init_db() -> None:
    """Run the mandatory DDL ahead of serving traffic."""
    with engine.begin() as conn:
        for statement in filter(None, DATABASE_DDL.strip().split(";\n\n")):
            conn.execute(text(statement + ";"))


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
