from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_TEXT_LLM_PROVIDER: ContextVar[str | None] = ContextVar("text_llm_provider_override", default=None)
_VISION_LLM_PROVIDER: ContextVar[str | None] = ContextVar("vision_llm_provider_override", default=None)
_OCR_PROVIDER: ContextVar[str | None] = ContextVar("ocr_provider_override", default=None)


@contextmanager
def provider_overrides(
    *,
    llm_provider: str | None = None,
    vision_llm_provider: str | None = None,
    ocr_provider: str | None = None,
) -> Iterator[None]:
    text_token = _TEXT_LLM_PROVIDER.set(llm_provider)
    vision_token = _VISION_LLM_PROVIDER.set(vision_llm_provider)
    ocr_token = _OCR_PROVIDER.set(ocr_provider)
    try:
        yield
    finally:
        _TEXT_LLM_PROVIDER.reset(text_token)
        _VISION_LLM_PROVIDER.reset(vision_token)
        _OCR_PROVIDER.reset(ocr_token)


def get_provider_overrides() -> tuple[str | None, str | None, str | None]:
    return _TEXT_LLM_PROVIDER.get(), _VISION_LLM_PROVIDER.get(), _OCR_PROVIDER.get()
