from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tuneai.schemas.score_ir import NoteEvent, ScoreIR

_ACC_SYMBOL = {"sharp": "#", "flat": "b", "natural": ""}
_WHITE_BGR = (255, 255, 255)
_BLACK_RGB = (0, 0, 0)


def render_output(
    original_image_bytes: bytes,
    original_score: ScoreIR,
    transposed_score: ScoreIR,
) -> bytes:
    nparr = np.frombuffer(original_image_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        _, buf = cv2.imencode(".png", np.full((200, 400, 3), 255, dtype=np.uint8))
        return buf.tobytes()
    patches: list[tuple[tuple[int, int, int, int], str]] = []
    for ev_orig, ev_trans in zip(original_score.events, transposed_score.events):
        if not isinstance(ev_orig, NoteEvent) or not isinstance(ev_trans, NoteEvent):
            continue
        if ev_orig.bbox is None or len(ev_orig.bbox) < 4:
            continue
        if (
            ev_orig.degree == ev_trans.degree
            and ev_orig.accidental == ev_trans.accidental
            and ev_orig.octave_shift == ev_trans.octave_shift
        ):
            continue
        if ev_trans.accidental not in _ACC_SYMBOL:
            raise ValueError(f"unsupported accidental: {ev_trans.accidental}")
        acc = _ACC_SYMBOL[ev_trans.accidental]
        patches.append((tuple(ev_orig.bbox), f"{acc}{ev_trans.degree}"))  # type: ignore[arg-type]
    if not patches:
        _, buf = cv2.imencode(".png", img_bgr)
        return buf.tobytes()
    pad = 3
    h, w = img_bgr.shape[:2]
    for (bx, by, bw, bh), _ in patches:
        x0 = max(0, bx - pad)
        y0 = max(0, by - pad)
        x1 = min(w, bx + bw + pad)
        y1 = min(h, by + bh + pad)
        cv2.rectangle(img_bgr, (x0, y0), (x1, y1), _WHITE_BGR, thickness=-1)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    for (bx, by, bw, bh), text in patches:
        font = _load_font(max(8, int(bh * 0.85)))
        draw.text((bx, by), text, fill=_BLACK_RGB, font=font)
    result_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode(".png", result_bgr)
    return buf.tobytes()


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()
