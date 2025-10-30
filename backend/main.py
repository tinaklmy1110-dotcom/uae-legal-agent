from __future__ import annotations

import os
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import get_session, init_db
from .models import LegalSlice as LegalSliceModel
from .rag import run_answer, run_search
from .schema import (
    AnswerResponse,
    Effective,
    Instrument,
    Jurisdiction,
    LegalSlice,
    SearchRequest,
    SearchResponse,
    Source,
    Structure,
    StructureLocators,
)


def get_db() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session


def orm_to_schema(record: LegalSliceModel) -> LegalSlice:
    locators = StructureLocators(
        part=record.part,
        chapter=record.chapter,
        section=record.section,
        article=record.article,
        rule=record.rule,
        clause=record.clause,
        item=record.item,
    )
    structure = Structure(
        granularity=record.granularity,
        path=record.path,
        locators=locators,
    )
    jurisdiction = Jurisdiction(
        level=record.level,
        name=record.name,
        emirate=record.emirate,
        freezone=record.freezone,
    )
    source = Source(
        portal=record.portal,
        url=record.url,
        gazette=record.gazette,
    )
    effective = Effective(
        from_date=record.effective_from.isoformat(),
        to_date=record.effective_to.isoformat() if record.effective_to else None,
        basis=None,
    )

    instrument = Instrument(
        type=record.type,
        number=record.number,
        year=record.year,
        title=record.title,
        issuer=record.issuer,
        official_language=record.official_language,
    )

    return LegalSlice(
        id=record.id,
        jurisdiction=jurisdiction,
        source=source,
        instrument=instrument,
        structure=structure,
        text_content=record.text_content,
        text_hash=record.text_hash,
        primary_lang=record.primary_lang,
        topics=record.topics or [],
        state=record.state,
        effective=effective,
        versions=[],
    )


app = FastAPI(title="UAE Legal Agent API", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/search", response_model=SearchResponse)
def search_endpoint(
    payload: SearchRequest,
    session: Session = Depends(get_db),
) -> SearchResponse:
    return run_search(session, payload)


@app.get("/get_by_id/{slice_id}", response_model=LegalSlice)
def get_by_id(
    slice_id: str,
    session: Session = Depends(get_db),
) -> LegalSlice:
    record = session.get(LegalSliceModel, slice_id)
    if not record:
        raise HTTPException(status_code=404, detail="Legal slice not found")
    return orm_to_schema(record)


@app.post("/answer", response_model=AnswerResponse)
def answer_endpoint(
    payload: SearchRequest,
    session: Session = Depends(get_db),
) -> AnswerResponse:
    return run_answer(session, payload)
