"""
像素回写（第五步，本地）。

职责分工：
  OpenCV  — 图像解码、白色矩形擦除、PNG 编码输出
  Pillow  — 字体加载、文字渲染（draw.text）

流程（每个发生变化的 bbox）：
  1. OpenCV cv2.rectangle 白色填充覆盖原数字
  2. 将当前帧转为 Pillow Image
  3. Pillow ImageFont + ImageDraw.text 在原位置渲染新数字
  4. 将结果转回 numpy 数组继续处理
  5. 所有 bbox 处理完毕后，OpenCV cv2.imencode 输出 PNG bytes
"""
from __future__ import annotations

import io

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
    """
    对所有发生变化的音符 bbox 执行像素回写，返回 PNG bytes。
    非变化区域保持原图不动。
    """
    # ── OpenCV：解码原图 ────────────────────────────────────────────────────
    nparr = np.frombuffer(original_image_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        _, buf = cv2.imencode(".png", np.full((200, 400, 3), 255, dtype=np.uint8))
        return buf.tobytes()

    # 收集需要回写的 (bbox, new_text) 对
    patches: list[tuple[tuple[int, int, int, int], str]] = []
    for ev_orig, ev_trans in zip(original_score.events, transposed_score.events):
        if not isinstance(ev_orig, NoteEvent) or not isinstance(ev_trans, NoteEvent):
            continue
        if ev_orig.bbox is None or len(ev_orig.bbox) < 4:
            continue
        if (ev_orig.degree == ev_trans.degree
                and ev_orig.accidental == ev_trans.accidental
                and ev_orig.octave_shift == ev_trans.octave_shift):
            continue

        acc = _ACC_SYMBOL.get(ev_trans.accidental, "")
        text = f"{acc}{ev_trans.degree}"
        patches.append((tuple(ev_orig.bbox), text))  # type: ignore[arg-type]

    if not patches:
        # 无变化，直接重编码返回
        _, buf = cv2.imencode(".png", img_bgr)
        return buf.tobytes()

    # ── OpenCV：批量白色填充擦除所有变化区域 ──────────────────────────────
    pad = 3
    h, w = img_bgr.shape[:2]
    for (bx, by, bw, bh), _ in patches:
        x0 = max(0, bx - pad)
        y0 = max(0, by - pad)
        x1 = min(w, bx + bw + pad)
        y1 = min(h, by + bh + pad)
        cv2.rectangle(img_bgr, (x0, y0), (x1, y1), _WHITE_BGR, thickness=-1)

    # ── Pillow：文字渲染 ────────────────────────────────────────────────────
    # BGR → RGB，转为 Pillow Image
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    for (bx, by, bw, bh), text in patches:
        font_size = max(8, int(bh * 0.85))
        font = _load_font(font_size)
        draw.text((bx, by), text, fill=_BLACK_RGB, font=font)

    # ── OpenCV：PNG 编码输出 ────────────────────────────────────────────────
    result_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode(".png", result_bgr)
    return buf.tobytes()


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """加载指定大小的字体；不可用时回退到 Pillow 默认字体。"""
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()
