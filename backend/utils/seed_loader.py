from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from ..db import get_session, init_db  # type: ignore[import]
    from ..models import LegalSlice as LegalSliceModel  # type: ignore[import]
    from ..search import embed  # type: ignore[import]
    from ..schema import LegalSlice  # type: ignore[import]
except ImportError:  # Fallback when executed as `python -m utils.seed_loader`
    from db import get_session, init_db  # type: ignore[import]
    from models import LegalSlice as LegalSliceModel  # type: ignore[import]
    from search import embed  # type: ignore[import]
    from schema import LegalSlice  # type: ignore[import]

from .text_clean import normalize_whitespace


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def load_seed_records(payload: List[Dict[str, Any]]) -> List[LegalSlice]:
    return [LegalSlice(**item) for item in payload]


def upsert_records(records: List[LegalSlice]) -> None:
    init_db()
    with get_session() as session:
        for record in records:
            locators = record.structure.locators
            effective = record.effective
            topics = list(record.topics or [])
            model = LegalSliceModel(
                id=record.id,
                level=record.jurisdiction.level,
                name=record.jurisdiction.name,
                emirate=record.jurisdiction.emirate,
                freezone=record.jurisdiction.freezone,
                portal=record.source.portal,
                url=record.source.url,
                gazette=record.source.gazette,
                type=record.instrument.type,
                number=record.instrument.number,
                year=record.instrument.year,
                title=record.instrument.title,
                issuer=record.instrument.issuer,
                official_language=record.instrument.official_language,
                granularity=record.structure.granularity,
                path=record.structure.path,
                part=locators.part,
                chapter=locators.chapter,
                section=locators.section,
                article=locators.article,
                rule=locators.rule,
                clause=locators.clause,
                item=locators.item,
                text_content=normalize_whitespace(record.text_content),
                text_hash=record.text_hash,
                primary_lang=record.primary_lang,
                topics=topics,
                state=record.state,
                effective_from=_parse_date(effective.from_date),
                effective_to=_parse_date(effective.to_date),
                vector_embedding=embed(record.text_content).tolist(),
            )
            session.merge(model)
        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load sample legal slice data into the Postgres store."
    )
    parser.add_argument(
        "payload",
        type=Path,
        help="Path to JSON payload matching schema.LegalSlice[]",
    )
    args = parser.parse_args()

    with args.payload.open("r", encoding="utf-8") as fh:
        raw_data = json.load(fh)

    if not isinstance(raw_data, list):
        raise ValueError("Expected list of legal slice objects.")

    records = load_seed_records(raw_data)
    upsert_records(records)


if __name__ == "__main__":
    main()
