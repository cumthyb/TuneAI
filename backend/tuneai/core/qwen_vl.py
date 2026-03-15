"""
Qwen-VL 调号识别（第二步 A，线上）。
通过 LangChain ChatOpenAI（OpenAI-compatible 模式）调用 Qwen-VL，
输入整张图，仅识别调号，输出结构化结果如 "G"。

配置来源：config.json > qwen_vl
  base_url     DashScope OpenAI-compatible 端点
  api_key      DashScope API Key
  model        视觉模型名称，默认 qwen-vl-max
  timeout_seconds
"""
from __future__ import annotations

import base64
import re

import cv2
import numpy as np
from pydantic import BaseModel, Field

from tuneai.logging_config import get_logger

_KEY_RE = re.compile(r"1\s*[=＝]\s*([A-G][#b♯♭]?)")
_TONIC_RE = re.compile(r"\b([A-G][#b]?)\b")

_PROMPT = (
    "这是一张简谱图片。请识别图中的调号，调号格式为 '1=X'（例如 1=C、1=G、1=Bb、1=F#）。\n"
    "只回答调号本身，例如：1=G\n"
    "如果无法确认，回答：unknown"
)


class KeySignatureResult(BaseModel):
    label: str = Field(description="完整调号，如 1=G、1=Bb")
    tonic: str = Field(description="主音，如 G、Bb、F#")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)


# 模块级单例
_llm_instance = None


def _get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = _create_llm()
    return _llm_instance


def _create_llm():
    from langchain_openai import ChatOpenAI
    from tuneai.config import get_qwen_vl_config

    cfg = get_qwen_vl_config()
    return ChatOpenAI(
        model=cfg.get("model", "qwen-vl-max"),
        api_key=cfg.get("api_key", "dummy"),
        base_url=cfg.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        timeout=float(cfg.get("timeout_seconds", 30)),
        temperature=0,
        max_tokens=64,
    )


def recognize_key_signature(image: np.ndarray) -> str:
    """
    输入灰度图，调用 Qwen-VL 识别调号。
    返回主音字符串如 "G"、"Bb"、"F#"；识别失败时返回 "C"（降级默认值）。
    """
    log = get_logger("qwen_vl")

    from tuneai.config import get_qwen_vl_config
    cfg = get_qwen_vl_config()

    if not cfg.get("api_key"):
        log.warning("qwen_vl: api_key 未配置，跳过调号识别，使用默认 C 调")
        return "C"

    # 编码图像为 base64 PNG
    _, buf = cv2.imencode(".png", image)
    b64 = base64.b64encode(buf.tobytes()).decode()

    try:
        from langchain_core.messages import HumanMessage

        llm = _get_llm()
        message = HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            },
            {"type": "text", "text": _PROMPT},
        ])

        response = llm.invoke([message])
        text = (response.content or "").strip()
        log.debug(f"qwen_vl raw response: {text!r}")
        return _parse_key(text)

    except Exception as e:
        log.warning(f"qwen_vl 调用失败 ({type(e).__name__}: {e})，使用默认 C 调")
        return "C"


def _parse_key(text: str) -> str:
    """从 Qwen-VL 回复中提取主音，归一化升降号写法。"""
    m = _KEY_RE.search(text)
    if m:
        return _normalize(m.group(1))
    m = _TONIC_RE.search(text)
    if m:
        return _normalize(m.group(1))
    return "C"


def _normalize(tonic: str) -> str:
    return tonic.replace("♯", "#").replace("♭", "b")
