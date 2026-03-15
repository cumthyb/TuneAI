"""
符号绑定、乐谱结构、输出 score IR。
"""
from __future__ import annotations

import re
import uuid
from typing import Optional

from tuneai.core.ocr import OCRToken
from tuneai.core.symbols import OctaveDot, DurationMark
from tuneai.logging_config import get_logger
from tuneai.schemas.score_ir import (
    BarlineEvent,
    Event,
    KeyChangeEvent,
    KeyInfo,
    Measure,
    NoteEvent,
    RestEvent,
    ScoreIR,
)

_KEY_PATTERN = re.compile(r"1\s*[=＝]\s*([A-G][#b♯♭]?)")
_NOTE_RE = re.compile(r"^[1-7]$")
_REST_RE = re.compile(r"^0$")


def bind_symbols(
    note_tokens: list[OCRToken],
    octave_dots: list[OctaveDot],
    duration_marks: list[DurationMark],
    accidentals: list[dict],
    barline_xs: list[int],
) -> list[Measure]:
    """
    将音符 token 与其周围的符号（八度点、时值横线、临时记号）绑定，
    按小节线分割为 Measure 列表。
    """
    log = get_logger("parser")

    # 按 x 坐标排序所有音符 token
    sorted_tokens = sorted(note_tokens, key=lambda t: (t.bbox[1], t.bbox[0]))
    sorted_barlines = sorted(barline_xs)

    events: list[Event] = []
    event_id = 0

    for tok in sorted_tokens:
        tx, ty, tw, th = tok.bbox
        cx = tx + tw // 2
        cy = ty + th // 2
        # 搜索窗口半径（约 1.5 字符宽）
        radius_x = max(tw, 10) * 1.5
        radius_y = max(th, 10) * 2.0

        # 绑定八度点
        oct_shift = 0
        for dot in octave_dots:
            if abs(dot.x - cx) <= radius_x:
                if dot.position == "above" and dot.y < ty:
                    oct_shift += 1
                elif dot.position == "below" and dot.y > ty + th:
                    oct_shift -= 1

        # 绑定临时记号
        accidental = "natural"
        for acc in accidentals:
            ax, ay, aw, ah = acc["bbox"]
            acx = ax + aw // 2
            acy = ay + ah // 2
            # 临时记号在音符左侧
            if ax + aw <= tx and abs(acx - tx) <= radius_x and abs(acy - cy) <= radius_y:
                accidental = acc["type"]
                break

        # 绑定时值横线
        dur_marks: list[str] = []
        for dm in duration_marks:
            dx, dy, dw, dh = dm.bbox
            if abs((dx + dw // 2) - cx) <= radius_x:
                dur_marks.append(dm.type)

        degree = int(tok.text)
        if _REST_RE.match(tok.text):
            ev = RestEvent(id=f"ev_{event_id}", confidence=tok.confidence)
        else:
            ev = NoteEvent(
                id=f"ev_{event_id}",
                degree=degree,
                accidental=accidental,
                octave_shift=oct_shift,
                duration_marks=dur_marks,
                bbox=tok.bbox,
                confidence=tok.confidence,
            )
        events.append(ev)
        event_id += 1

    # 按小节线分割
    measures = _split_into_measures(events, note_tokens, sorted_barlines)
    return measures


def _split_into_measures(
    events: list[Event],
    note_tokens: list[OCRToken],
    barline_xs: list[int],
) -> list[Measure]:
    """根据小节线 x 坐标将 events 分配到各小节。"""
    if not events:
        return [Measure(number=1, events=[])]

    # 为每个 event 找其 x 坐标
    event_xs: list[int] = []
    tok_map = {(t.bbox[0], t.bbox[1]): t for t in note_tokens}

    for ev in events:
        if isinstance(ev, NoteEvent) and ev.bbox:
            event_xs.append(ev.bbox[0] + ev.bbox[2] // 2)
        else:
            event_xs.append(-1)

    if not barline_xs:
        return [Measure(number=1, events=list(events))]

    measures: list[Measure] = []
    measure_num = 1
    current_events: list[Event] = []
    bar_idx = 0

    for ev, ex in zip(events, event_xs):
        # 插入小节线事件
        while bar_idx < len(barline_xs) and ex > barline_xs[bar_idx]:
            measures.append(Measure(number=measure_num, events=current_events))
            current_events = []
            measure_num += 1
            bar_idx += 1
        current_events.append(ev)

    if current_events:
        measures.append(Measure(number=measure_num, events=current_events))

    return measures if measures else [Measure(number=1, events=list(events))]


def parse_score(
    note_tokens: list[OCRToken],
    symbols: dict,
    key_token: Optional[OCRToken],
) -> ScoreIR:
    """
    组装 ScoreIR。
    symbols = {"octave_dots": ..., "duration_marks": ..., "accidentals": ..., "barlines": ...}
    """
    log = get_logger("parser")

    # 解析调号
    source_tonic = "C"
    source_label = "1=C"
    if key_token:
        m = _KEY_PATTERN.search(key_token.text)
        if m:
            raw = m.group(1).replace("♯", "#").replace("♭", "b")
            source_tonic = raw
            source_label = f"1={raw}"
        else:
            log.warning(f"无法从 OCR 结果解析调号: {key_token.text!r}，默认使用 1=C")
    else:
        log.warning("未找到调号 token，默认使用 1=C")

    measures = bind_symbols(
        note_tokens,
        symbols.get("octave_dots", []),
        symbols.get("duration_marks", []),
        symbols.get("accidentals", []),
        symbols.get("barlines", []),
    )

    source_key = KeyInfo(label=source_label, tonic=source_tonic)
    return ScoreIR(
        score_id=str(uuid.uuid4()),
        source_key=source_key,
        target_key=source_key,  # 初始与 source 相同，由 music.transpose_score_ir 更新
        measures=measures,
    )
