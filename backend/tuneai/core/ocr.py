"""
阿里云 OCR 封装（第二步 B，线上）：全字符 bbox 识别。
输入整张预处理图，输出所有字符的 bbox + 识别内容。
"""
from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass

import cv2
import numpy as np

from tuneai.logging_config import get_logger


@dataclass
class OcrChar:
    text: str
    bbox: list[int]       # [x, y, w, h]
    confidence: float


def run_ocr(image: np.ndarray) -> list[OcrChar]:
    """
    调用阿里云 OCR，返回全字符识别结果列表。
    失败时返回空列表（不抛异常），由调用方处理降级。
    """
    log = get_logger("ocr")

    from tuneai.config import get_alibaba_ocr_config
    cfg = get_alibaba_ocr_config()

    if not cfg.get("access_key_id") or not cfg.get("access_key_secret"):
        log.warning("alibaba_ocr: access_key 未配置，跳过 OCR")
        return []

    # 编码图像为 PNG bytes
    _, buf = cv2.imencode(".png", image)
    image_bytes = buf.tobytes()

    try:
        from alibabacloud_ocr_api20210707 import models as ocr_models
        from alibabacloud_ocr_api20210707.client import Client
        from alibabacloud_tea_openapi import models as openapi_models

        openapi_cfg = openapi_models.Config(
            access_key_id=cfg.get("access_key_id", ""),
            access_key_secret=cfg.get("access_key_secret", ""),
            endpoint=cfg.get("endpoint", "ocr-api.cn-hangzhou.aliyuncs.com"),
        )
        client = Client(openapi_cfg)

        request = ocr_models.RecognizeGeneralRequest(body=io.BytesIO(image_bytes))
        response = client.recognize_general(request)

        chars = _parse_response(response)
        log.debug(f"alibaba_ocr: {len(chars)} chars recognized")
        return chars

    except Exception as e:
        log.warning(f"alibaba_ocr 调用失败 ({type(e).__name__}: {e})")
        return []


def _parse_response(response) -> list[OcrChar]:
    """
    解析阿里云 OCR 响应。
    阿里云 RecognizeGeneral 返回 body.data 为 JSON 字符串，
    其中 blocks[] 包含每个文字区域的 text 和坐标。
    """
    chars: list[OcrChar] = []
    try:
        raw = getattr(response.body, "data", None) or ""
        if not raw:
            return chars

        data = json.loads(raw) if isinstance(raw, str) else raw
        blocks = data.get("blocks", [])

        for block in blocks:
            text = (block.get("text") or block.get("blockText") or "").strip()
            if not text:
                continue

            confidence = float(block.get("confidence", 1.0))
            bbox = _extract_bbox(block)
            if bbox is None:
                continue

            # 对多字符 block 按字符拆分（每个字符用相同 bbox，精度受限）
            for ch in text:
                chars.append(OcrChar(text=ch, bbox=bbox, confidence=confidence))

    except Exception as e:
        get_logger("ocr").debug(f"_parse_response error: {e}")

    return chars


def _extract_bbox(block: dict) -> list[int] | None:
    """从 block 中提取 [x, y, w, h]，兼容多种字段格式。"""
    # 格式 A: blockCoordinate with pointXxx
    coord = block.get("blockCoordinate")
    if coord:
        try:
            xs = [coord[k]["x"] for k in ("pointTopLeft", "pointTopRight",
                                           "pointBottomLeft", "pointBottomRight")]
            ys = [coord[k]["y"] for k in ("pointTopLeft", "pointTopRight",
                                           "pointBottomLeft", "pointBottomRight")]
            return [int(min(xs)), int(min(ys)),
                    int(max(xs) - min(xs)), int(max(ys) - min(ys))]
        except Exception:
            pass

    # 格式 B: textRectangle with x/y/width/height
    rect = block.get("textRectangle")
    if rect:
        try:
            return [int(rect["x"]), int(rect["y"]),
                    int(rect["width"]), int(rect["height"])]
        except Exception:
            pass

    # 格式 C: direct x/y/w/h fields
    if all(k in block for k in ("x", "y", "w", "h")):
        return [int(block["x"]), int(block["y"]),
                int(block["w"]), int(block["h"])]

    return None
