from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.orm import Session

from . import search
from .models import LegalSlice
from .schema import AnswerResponse, Citation, SearchRequest, SearchResponse
from .utils.text_clean import truncate_for_snippet

DISCLAIMER = (
    "信息检索工具，非法律意见；以官方文本为准（DIFC/ADGM 英文为权威；联邦英文多为参考译文）"
)


def build_citation(slice_obj: LegalSlice) -> Citation:
    snippet = truncate_for_snippet(slice_obj.text_content, max_chars=200)
    return Citation(
        id=slice_obj.id,
        instrument_title=slice_obj.title,
        structure_path=slice_obj.path,
        source_url=slice_obj.url,
        gazette=slice_obj.gazette,
        snippet=snippet,
    )


def _materialise(
    ranked_results: List[Tuple[LegalSlice, float]]
) -> List[LegalSlice]:
    """Extract ORM entities from scoring tuples."""
    return [record for record, _ in ranked_results]


def run_search(session: Session, payload: SearchRequest) -> SearchResponse:
    filters = search.to_filters(
        jurisdiction=payload.jurisdiction,
        topics=payload.topics,
        as_of=payload.as_of,
    )
    ranked = search.hybrid_search(session, payload.query, filters, limit=8)
    slices = _materialise(ranked)
    citations = [build_citation(item) for item in slices]
    return SearchResponse(query=payload.query, items=citations)


def synthesise_answer(payload: SearchRequest, citations: List[Citation]) -> str:
    if not citations:
        return "未检索到与查询匹配的官方条文，请尝试调整关键词。"

    fragments = []
    for citation in citations[:3]:
        fragments.append(
            f"{citation.instrument_title}（{citation.structure_path}）摘要：{citation.snippet}"
        )

    joined = "；".join(fragments)
    return f"根据所检索到的官方条文（非法律意见），{joined}"


def run_answer(session: Session, payload: SearchRequest) -> AnswerResponse:
    response = run_search(session, payload)
    answer_text = synthesise_answer(payload, response.items)
    return AnswerResponse(
        answer=answer_text,
        items=response.items,
        disclaimer=DISCLAIMER,
    )
