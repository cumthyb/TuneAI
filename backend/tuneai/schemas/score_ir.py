"""
乐谱 IR：events、key。
新流程：flat 事件列表，无 measures 层级。
"""
from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class KeyInfo(BaseModel):
    label: str                    # e.g. "1=C"
    tonic: str                    # e.g. "C"
    mode: str = "major"
    bbox: Optional[list[int]] = None
    confidence: float = 1.0


class NoteEvent(BaseModel):
    id: str
    type: Literal["note"] = "note"
    degree: int                   # 1-7
    accidental: str = "natural"   # "natural" | "sharp" | "flat"
    octave_shift: int = 0         # +1 高八度点, -1 低八度点
    bbox: Optional[list[int]] = None
    confidence: float = 1.0


class RestEvent(BaseModel):
    id: str
    type: Literal["rest"] = "rest"
    bbox: Optional[list[int]] = None
    confidence: float = 1.0


Event = Annotated[
    Union[NoteEvent, RestEvent],
    Field(discriminator="type"),
]


class ScoreIR(BaseModel):
    score_id: str
    source_key: KeyInfo
    target_key: KeyInfo
    events: list[Event] = Field(default_factory=list)
