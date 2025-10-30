from __future__ import annotations

from datetime import date
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .db import PGVECTOR_DIM


class Base(DeclarativeBase):
    """Shared base metadata for SQLAlchemy declarative models."""


class LegalSlice(Base):
    __tablename__ = "legal_slice"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    level: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    emirate: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    freezone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portal: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    gazette: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    number: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    issuer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    official_language: Mapped[str] = mapped_column(String, nullable=False)
    granularity: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    part: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    chapter: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    article: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rule: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    clause: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    item: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String, nullable=False)
    primary_lang: Mapped[str] = mapped_column(String, nullable=False)
    topics: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    vector_embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(PGVECTOR_DIM), nullable=True
    )
