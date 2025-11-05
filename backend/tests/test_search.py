from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import delete

from backend.db import get_session, init_db
from backend.models import LegalSlice as LegalSliceModel
from backend.search import hybrid_search, to_filters, vector_search


@pytest.fixture(autouse=True)
def clean_table():
    init_db()
    with get_session() as session:
        session.execute(delete(LegalSliceModel))
        session.commit()
    yield


def _create_slice(
    *,
    slice_id: str,
    text: str,
    effective_from: date,
    effective_to: date | None = None,
):
    from backend.search import embed

    with get_session() as session:
        session.add(
            LegalSliceModel(
                id=slice_id,
                level="emirate",
                name="Dubai",
                emirate="Dubai",
                freezone=None,
                portal="Dubai Legislation Portal",
                url="https://example.com",
                gazette="Dubai Official Gazette",
                type="Dubai Law",
                number="1",
                year=2020,
                title="Test Law",
                issuer=None,
                official_language="Arabic",
                granularity="article",
                path="Article 1",
                part=None,
                chapter=None,
                section=None,
                article="1",
                rule=None,
                clause=None,
                item=None,
                text_content=text,
                text_hash="sha256:test",
                primary_lang="ar",
                topics=["compliance"],
                state="in_force",
                effective_from=effective_from,
                effective_to=effective_to,
                vector_embedding=embed(text).tolist(),
            )
        )
        session.commit()


def test_vector_search_returns_result():
    today = date.today()
    _create_slice(slice_id="slice-1", text="Tenancy deposit procedures", effective_from=today)

    with get_session() as session:
        filters = to_filters(jurisdiction="Dubai")
        results = vector_search(session, "tenancy deposit", filters, k=5)

    assert results, "Expected vector search to return at least one result"
    ids = [row[0].id for row in results]
    assert "slice-1" in ids


def test_as_of_filter_excludes_future_entries():
    today = date.today()
    _create_slice(slice_id="slice-active", text="Rules currently active", effective_from=today - timedelta(days=10))
    _create_slice(
        slice_id="slice-future",
        text="Future rules",
        effective_from=today + timedelta(days=10),
    )

    with get_session() as session:
        filters = to_filters(jurisdiction="Dubai", as_of=today.isoformat())
        ranked = hybrid_search(session, "rules", filters, limit=10)

    returned_ids = [row[0].id for row in ranked]
    assert "slice-active" in returned_ids
    assert "slice-future" not in returned_ids
