from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel, HttpUrl


JurisdictionLevel = Literal["federal", "emirate", "freezone"]


class Jurisdiction(BaseModel):
    level: JurisdictionLevel
    name: str  # UAE / Dubai / Abu Dhabi / DIFC / ADGM ...
    emirate: Optional[str] = None
    freezone: Optional[str] = None


class Source(BaseModel):
    portal: str  # 官方来源名
    url: HttpUrl
    gazette: Optional[str] = None


class Instrument(BaseModel):
    type: str
    number: str
    year: int
    title: str
    issuer: Optional[str] = None
    official_language: Literal["Arabic", "English"]


class StructureLocators(BaseModel):
    part: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    article: Optional[str] = None
    rule: Optional[str] = None
    clause: Optional[str] = None
    item: Optional[str] = None


class Structure(BaseModel):
    granularity: Literal["article", "clause", "item", "rule", "section"]
    path: str
    locators: StructureLocators


class Effective(BaseModel):
    from_date: str
    to_date: Optional[str] = None
    basis: Optional[
        Literal["gazette_publication", "explicit_article", "commencement_order"]
    ] = None


class VersionItem(BaseModel):
    version_id: str
    event: Literal["enacted", "amended", "consolidated", "repealed"]
    date: str
    by_instrument: Optional[str] = None
    by_url: Optional[str] = None


class LegalSlice(BaseModel):
    id: str
    jurisdiction: Jurisdiction
    source: Source
    instrument: Instrument
    structure: Structure
    text_content: str
    text_hash: str
    primary_lang: Literal["ar", "en"]
    topics: List[str] = []
    state: Literal["in_force", "amended", "repealed", "unknown"] = "in_force"
    effective: Effective
    versions: List[VersionItem] = []


class SearchRequest(BaseModel):
    query: str
    jurisdiction: Optional[str] = None  # e.g., "federal", "Dubai", "DIFC"
    topics: Optional[List[str]] = None
    as_of: Optional[str] = None  # YYYY-MM-DD


class Citation(BaseModel):
    id: str
    instrument_title: str
    structure_path: str
    source_url: str
    gazette: Optional[str] = None
    snippet: str


class SearchResponse(BaseModel):
    query: str
    items: List[Citation]


class AnswerResponse(BaseModel):
    answer: str
    items: List[Citation]
    disclaimer: str
