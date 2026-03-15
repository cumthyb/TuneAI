"""
局部擦除、字形绘制、原位贴回、导出 PNG。
"""
from __future__ import annotations

import io
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tuneai.schemas.score_ir import NoteEvent, ScoreIR

# 升降号文字映射（使用 Unicode 字符或 ASCII 替代）
_ACC_SYMBOL = {"sharp": "#", "flat": "b", "natural": ""}


def render_output(
    original_image: np.ndarray,
    original_score: ScoreIR,
    transposed_score: ScoreIR,
) -> bytes:
    """
    对所有发生变化的音符区域：
    1. 扩边 2-4px
    2. 背景填充（局部均值或白色）
    3. 在 Pillow 画布上用默认字体绘制新字符
    4. 按原 bbox 基线贴回
    5. 导出 PNG bytes
    """
    if original_image is None:
        # 如果原图解码失败，返回空白图
        blank = Image.new("RGB", (400, 200), color=(255, 255, 255))
        buf = io.BytesIO()
        blank.save(buf, format="PNG")
        return buf.getvalue()

    # 转为 Pillow Image（RGB）
    if len(original_image.shape) == 2:
        img_rgb = cv2.cvtColor(original_image, cv2.COLOR_GRAY2RGB)
    else:
        img_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    # 构建 (measure_idx, event_idx) → transposed event 映射
    for m_orig, m_trans in zip(original_score.measures, transposed_score.measures):
        for ev_orig, ev_trans in zip(m_orig.events, m_trans.events):
            if not isinstance(ev_orig, NoteEvent) or not isinstance(ev_trans, NoteEvent):
                continue
            if ev_orig.bbox is None or len(ev_orig.bbox) < 4:
                continue

            # 判断是否有变化
            orig_tokens = ev_orig.render_tokens
            trans_tokens = ev_trans.render_tokens
            if orig_tokens == trans_tokens and ev_orig.degree == ev_trans.degree:
                continue

            bx, by, bw, bh = ev_orig.bbox
            pad = 3
            x0 = max(0, bx - pad)
            y0 = max(0, by - pad)
            x1 = min(pil_img.width, bx + bw + pad)
            y1 = min(pil_img.height, by + bh + pad)

            # 采样背景色（区域四角均值）
            bg_color = _sample_background(pil_img, x0, y0, x1, y1)

            # 填充背景
            draw.rectangle([x0, y0, x1, y1], fill=bg_color)

            # 计算字体大小（根据 bbox 高度估算）
            font_size = max(8, int(bh * 0.85))
            try:
                font = ImageFont.load_default(size=font_size)
            except TypeError:
                font = ImageFont.load_default()

            # 组装文字
            acc = _ACC_SYMBOL.get(ev_trans.accidental, "")
            text = f"{acc}{ev_trans.degree}"
            if ev_trans.octave_shift > 0:
                text = "·" * ev_trans.octave_shift + text
            elif ev_trans.octave_shift < 0:
                text = text + "·" * abs(ev_trans.octave_shift)

            # 在 bbox 中心绘制
            draw.text((bx, by), text, fill=(0, 0, 0), font=font)

    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


def _sample_background(img: Image.Image, x0: int, y0: int, x1: int, y1: int) -> tuple:
    """采样图像区域的背景色（四角像素均值）。"""
    corners = []
    for cx, cy in [(x0, y0), (x1 - 1, y0), (x0, y1 - 1), (x1 - 1, y1 - 1)]:
        cx = max(0, min(cx, img.width - 1))
        cy = max(0, min(cy, img.height - 1))
        corners.append(img.getpixel((cx, cy)))

    if not corners:
        return (255, 255, 255)

    avg = tuple(int(sum(c[i] for c in corners) / len(corners)) for i in range(3))
    return avg
