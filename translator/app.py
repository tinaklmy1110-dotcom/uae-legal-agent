from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import MarianMTModel, MarianTokenizer

MODEL_NAME = os.getenv("TRANSLATOR_MODEL", "Helsinki-NLP/opus-mt-en-zh")
MAX_LENGTH = int(os.getenv("TRANSLATOR_MAX_LENGTH", "1024"))

app = FastAPI(title="Translation Service", version="1.0.0")


class TranslateRequest(BaseModel):
    texts: List[str] = Field(..., description="List of English sentences to translate")


class TranslateResponse(BaseModel):
    translations: List[str]


@lru_cache(maxsize=1)
def get_pipeline():
    tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
    model = MarianMTModel.from_pretrained(MODEL_NAME)
    return tokenizer, model


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest) -> TranslateResponse:
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts must not be empty")

    tokenizer, model = get_pipeline()
    translations: List[str] = []

    for text in req.texts:
        if not text.strip():
            translations.append("")
            continue
        batch = tokenizer(
            [text],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
        )
        generated = model.generate(**batch, max_length=MAX_LENGTH)
        translated_text = tokenizer.decode(generated[0], skip_special_tokens=True)
        translations.append(translated_text)

    return TranslateResponse(translations=translations)


@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
