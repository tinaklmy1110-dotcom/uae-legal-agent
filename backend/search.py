from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
from dateutil import parser as date_parser
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from .db import PGVECTOR_DIM, PGVECTOR_METRIC
from .models import LegalSlice


EMBED_DIM = PGVECTOR_DIM


@dataclass
class SearchFilters:
    jurisdiction: Optional[str] = None
    topics: Optional[List[str]] = None
    as_of: Optional[date] = None


def parse_as_of(as_of: Optional[str]) -> Optional[date]:
    if not as_of:
        return None
    return date_parser.isoparse(as_of).date()


def embed(text: str) -> np.ndarray:
    """Deterministic placeholder embedding based on hashing."""
    if not text:
        return np.zeros(EMBED_DIM, dtype=np.float32)
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    repeats = math.ceil(EMBED_DIM / values.size)
    tiled = np.tile(values, repeats)[:EMBED_DIM]
    normalized = (tiled / 255.0) - 0.5
    norm = np.linalg.norm(normalized)
    if norm == 0:
        return normalized
    return normalized / norm


def _build_filtered_query(
    filters: SearchFilters,
) -> List:
    conditions: List = [LegalSlice.state.in_(["in_force", "amended"])]

    if filters.jurisdiction:
        value = filters.jurisdiction.strip().lower()
        if value:
            conditions.append(
                or_(
                    func.lower(LegalSlice.level) == value,
                    func.lower(LegalSlice.name) == value,
                    func.lower(LegalSlice.emirate) == value,
                    func.lower(LegalSlice.freezone) == value,
                )
            )

    if filters.topics:
        conditions.append(LegalSlice.topics.contains(filters.topics))

    if filters.as_of:
        conditions.append(LegalSlice.effective_from <= filters.as_of)
        conditions.append(
            or_(
                LegalSlice.effective_to.is_(None),
                LegalSlice.effective_to > filters.as_of,
            )
        )

    return conditions


def _metric_expression(query_vector: List[float]):
    if PGVECTOR_METRIC == "euclidean":
        return LegalSlice.vector_embedding.l2_distance(query_vector).label("distance"), "asc"
    if PGVECTOR_METRIC == "ip":
        return (
            LegalSlice.vector_embedding.max_inner_product(query_vector).label("similarity"),
            "desc",
        )
    # default cosine
    return LegalSlice.vector_embedding.cosine_distance(query_vector).label("distance"), "asc"


def _score_from_measure(value: float) -> float:
    if PGVECTOR_METRIC == "euclidean":
        return 1.0 / (1.0 + float(value))
    if PGVECTOR_METRIC == "ip":
        return float(value)
    # cosine
    return 1.0 - float(value)


def vector_search(
    session: Session, query: str, filters: SearchFilters, k: int = 8
) -> Sequence[Tuple[LegalSlice, float]]:
    query_vector = embed(query).tolist()
    measure_column, ordering = _metric_expression(query_vector)
    stmt = (
        select(LegalSlice, measure_column)
        .where(LegalSlice.vector_embedding.is_not(None))
        .limit(k)
    )
    conditions = _build_filtered_query(filters)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    if ordering == "desc":
        stmt = stmt.order_by(measure_column.desc())
    else:
        stmt = stmt.order_by(measure_column.asc())

    rows = session.execute(stmt).all()
    results: List[Tuple[LegalSlice, float]] = []
    for slice_obj, measurement in rows:
        if measurement is None:
            continue
        score = _score_from_measure(float(measurement))
        results.append((slice_obj, score))
    return results


def keyword_search(
    session: Session, query: str, filters: SearchFilters, k: int = 16
) -> Sequence[Tuple[LegalSlice, float]]:
    terms = [term for term in re.split(r"\s+", query) if term]
    if not terms:
        return []

    score_expr = None
    term_conditions = []
    for term in terms:
        pattern = f"%{term}%"
        term_condition = or_(
            LegalSlice.title.ilike(pattern),
            LegalSlice.path.ilike(pattern),
            LegalSlice.text_content.ilike(pattern),
        )
        term_conditions.append(term_condition)
        term_score = (
            case((LegalSlice.title.ilike(pattern), 3), else_=0)
            + case((LegalSlice.path.ilike(pattern), 2), else_=0)
            + case((LegalSlice.text_content.ilike(pattern), 1), else_=0)
        )
        score_expr = term_score if score_expr is None else score_expr + term_score

    stmt = select(LegalSlice, score_expr.label("score"))
    if score_expr is None:
        stmt = stmt.limit(0)
        return []

    stmt = stmt.where(and_(*term_conditions))

    conditions = _build_filtered_query(filters)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(score_expr.desc(), LegalSlice.year.desc()).limit(k)
    rows = session.execute(stmt).all()
    return rows


def hybrid_search(
    session: Session, query: str, filters: SearchFilters, limit: int = 10
) -> List[Tuple[LegalSlice, float]]:
    vector_results = vector_search(session, query, filters, k=min(limit, 8))
    keyword_results = keyword_search(session, query, filters, k=min(limit * 2, 16))

    combined: dict[str, Tuple[LegalSlice, float]] = {}

    for rank, (slice_obj, score) in enumerate(vector_results):
        base_score = 1.2 / (1 + rank)
        base_score += max(0.0, float(score))
        combined[slice_obj.id] = (slice_obj, base_score)

    for rank, (slice_obj, kw_score) in enumerate(keyword_results):
        increment = 0.8 / (1 + rank)
        if isinstance(kw_score, (int, float)):
            increment += float(kw_score)
        if slice_obj.id in combined:
            existing_slice, existing_score = combined[slice_obj.id]
            combined[slice_obj.id] = (existing_slice, existing_score + increment)
        else:
            combined[slice_obj.id] = (slice_obj, increment)

    # Prioritise records with explicit jurisdiction signal
    for slice_id, (slice_obj, score) in list(combined.items()):
        if filters.jurisdiction:
            combined[slice_id] = (slice_obj, score + 0.5)

    ranked = sorted(combined.values(), key=lambda item: item[1], reverse=True)
    return ranked[:limit]


def to_filters(
    jurisdiction: Optional[str] = None,
    topics: Optional[List[str]] = None,
    as_of: Optional[str] = None,
) -> SearchFilters:
    parsed_as_of = parse_as_of(as_of) if as_of else None
    return SearchFilters(
        jurisdiction=jurisdiction,
        topics=topics,
        as_of=parsed_as_of,
    )
