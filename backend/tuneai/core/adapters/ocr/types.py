from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OcrChar:
    text: str
    bbox: list[int]
    confidence: float
