"""
乐谱 IR：measures、events、key（与执行方案 §7 一致）。
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
    octave_shift: int = 0         # +1 high dot, -1 low dot
    duration_marks: list[str] = Field(default_factory=list)
    grace: bool = False
    bbox: Optional[list[int]] = None
    confidence: float = 1.0
    decoded_pitch_pc: Optional[int] = None
    decoded_pitch_octave: Optional[int] = None
    transposed_pitch_pc: Optional[int] = None
    transposed_pitch_octave: Optional[int] = None
    render_tokens: list[str] = Field(default_factory=list)


class RestEvent(BaseModel):
    id: str
    type: Literal["rest"] = "rest"
    symbol: int = 0               # 0 = standard rest
    bbox: Optional[list[int]] = None
    confidence: float = 1.0


class KeyChangeEvent(BaseModel):
    id: str
    type: Literal["key_change"] = "key_change"
    label: str
    tonic: str
    bbox: Optional[list[int]] = None
    confidence: float = 1.0


class BarlineEvent(BaseModel):
    id: str
    type: Literal["barline"] = "barline"
    bbox: Optional[list[int]] = None


Event = Annotated[
    Union[NoteEvent, RestEvent, KeyChangeEvent, BarlineEvent],
    Field(discriminator="type"),
]


class Measure(BaseModel):
    number: int
    events: list[Event] = Field(default_factory=list)


class ScoreIR(BaseModel):
    score_id: str
    source_key: KeyInfo
    target_key: KeyInfo
    measures: list[Measure] = Field(default_factory=list)
