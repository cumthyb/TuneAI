"""
PaddleOCR 封装，数字与调号文本，候选+bbox+置信度。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from tuneai.logging_config import get_logger

_ocr_instance = None
_logger = None


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        from tuneai.config import get_ocr_config
        cfg = get_ocr_config()
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(
            use_angle_cls=False,
            lang="ch",
            use_gpu=cfg.get("use_gpu", False),
            det_db_thresh=cfg.get("det_db_thresh", 0.3),
            rec_batch_num=cfg.get("rec_batch_num", 6),
            show_log=False,
        )
    return _ocr_instance


@dataclass
class OCRToken:
    text: str
    bbox: list[int]            # [x, y, w, h]
    confidence: float


_KEY_PATTERN = re.compile(r"1\s*[=＝]\s*([A-G][#b♯♭]?)")
_NOTE_PATTERN = re.compile(r"^[0-7]$")


def run_ocr(image_region: np.ndarray) -> list[OCRToken]:
    """PaddleOCR 封装；返回所有识别到的 token。"""
    log = get_logger("ocr")
    ocr = _get_ocr()

    try:
        results = ocr.ocr(image_region, cls=False)
    except Exception as e:
        log.warning(f"OCR failed: {e}")
        return []

    tokens: list[OCRToken] = []
    if not results or results[0] is None:
        return tokens

    for line in results[0]:
        if line is None:
            continue
        try:
            polygon, (text, conf) = line
            # polygon: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            x = int(min(xs))
            y = int(min(ys))
            w = int(max(xs) - min(xs))
            h = int(max(ys) - min(ys))
            tokens.append(OCRToken(text=text.strip(), bbox=[x, y, w, h], confidence=float(conf)))
        except Exception as e:
            log.debug(f"skip malformed OCR line: {e}")

    return tokens


def extract_key_signature(tokens: list[OCRToken]) -> Optional[OCRToken]:
    """
    在 tokens 中寻找调号（如 "1=C"、"1=G#"），
    返回页首最高置信度匹配，或 None。
    """
    candidates = []
    for tok in tokens:
        m = _KEY_PATTERN.search(tok.text)
        if m:
            candidates.append(tok)

    if not candidates:
        return None
    # 取置信度最高的（页首行优先可通过 y 坐标进一步过滤）
    return max(candidates, key=lambda t: t.confidence)


def extract_note_digits(tokens: list[OCRToken]) -> list[OCRToken]:
    """过滤出单个 0-7 数字的 token（简谱音符）。"""
    return [t for t in tokens if _NOTE_PATTERN.match(t.text)]
