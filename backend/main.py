from __future__ import annotations

import os
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3001")
frontend_origins_raw = os.getenv("FRONTEND_ORIGINS")
allowed_origins = (
    [
        origin.strip()
        for origin in frontend_origins_raw.split(",")
        if origin.strip()
    ]
    if frontend_origins_raw
    else [frontend_origin]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root() -> JSONResponse:
    return JSONResponse(
        {"message": "UAE Legal Agent API", "docs_url": "/docs", "status": "ok"}
    )


@app.get("/healthz", include_in_schema=False)
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


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

from pydantic import BaseModel
import httpx

TRANSLATOR_BASE_URL = os.getenv("TRANSLATOR_BASE_URL")
TRANSLATOR_TIMEOUT = float(os.getenv("TRANSLATOR_TIMEOUT", "15"))


class TranslatePayload(BaseModel):
    texts: list[str]


class TranslateRequest(BaseModel):
    texts: list[str]


class TranslateResponse(BaseModel):
    translations: list[str]


@app.post("/translate", response_model=TranslateResponse)
async def translate_endpoint(payload: TranslateRequest) -> TranslateResponse:
    if not payload.texts:
        raise HTTPException(status_code=400, detail="texts must not be empty")

    if not TRANSLATOR_BASE_URL:
        raise HTTPException(status_code=503, detail="Translation service unavailable")

    try:
        request_body = TranslatePayload(texts=payload.texts)
        payload_json = (
            request_body.model_dump()  # type: ignore[attr-defined]
            if hasattr(request_body, "model_dump")
            else request_body.dict()
        )

        async with httpx.AsyncClient(timeout=TRANSLATOR_TIMEOUT) as client:
            response = await client.post(
                f"{TRANSLATOR_BASE_URL}/translate",
                json=payload_json,
            )
        response.raise_for_status()
        data = response.json()
        translations = data.get("translations")
        if not isinstance(translations, list):
            raise ValueError("Invalid response format from translator")
        return TranslateResponse(translations=[str(item) for item in translations])
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Translation service error: {exc.response.text}",
        ) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=502, detail="Translation service unavailable") from exc
