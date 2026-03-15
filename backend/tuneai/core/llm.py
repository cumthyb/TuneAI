"""
LangChain 封装、结构化输出、低置信度纠错与补全。

依赖版本（见 pyproject.toml）：
  langchain        ^1.2
  langchain-core   ^1.2
  langchain-openai ^1.1   （需要 openai ^2.0）
  openai           ^2.0

设计要点：
  - ChatOpenAI 通过 base_url + api_key 支持任意 OpenAI-compatible 端点（Ollama/LiteLLM 等）
  - structured_output_method 可配置：
      "function_calling"  默认，兼容最广（包括 Ollama）
      "json_schema"       OpenAI 原生结构化输出，更严格，不支持所有端点
  - disable_parallel_tool_calls=true 时关闭 parallel_tool_calls，
    Ollama 等非标准端点不支持该参数，必须禁用
  - LLM 实例为模块级单例；两个任务共用同一实例
  - 所有调用均有异常捕获：任务 A 回退到正则解析，任务 B 原样返回 tokens
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from tuneai.logging_config import get_logger


# ---------------------------------------------------------------------------
# 输出 schema（Pydantic v2）
# ---------------------------------------------------------------------------

class KeyCorrectionResult(BaseModel):
    tonic: str   = Field(description="识别到的主音，如 C、G#、Bb")
    label: str   = Field(description="完整调号标记，如 1=C、1=G#")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str   = Field(default="", description="补充说明")


class MeasureCorrectionResult(BaseModel):
    events: list[dict] = Field(description="补全后的事件列表")
    confidence: float  = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str         = Field(default="", description="补充说明")


# ---------------------------------------------------------------------------
# LLM 单例
# ---------------------------------------------------------------------------

_llm_instance = None


def _create_llm():
    """
    根据 config.json 构造 ChatOpenAI 实例。

    关键参数说明：
      base_url   — 指向任意 OpenAI-compatible 端点（留空则用官方 OpenAI）
      api_key    — Ollama 可填任意字符串（如 "ollama"）
      disabled_params — 禁用 non-standard 端点不支持的参数
    """
    from langchain_openai import ChatOpenAI
    from tuneai.config import get_llm_config, get_api_key

    cfg = get_llm_config()
    base_url = cfg.get("base_url") or None
    api_key  = cfg.get("api_key") or get_api_key("openai") or "dummy"

    # openai 2.x: timeout 传 float（秒）即可，langchain-openai 1.1 透传给 httpx
    timeout: float = float(cfg.get("timeout_seconds", 30))

    # Ollama 等非标准端点不支持 parallel_tool_calls，需要禁用
    disabled_params: dict | None = None
    if cfg.get("disable_parallel_tool_calls", False):
        disabled_params = {"parallel_tool_calls": None}

    return ChatOpenAI(
        model=cfg.get("model", "gpt-4o-mini"),
        base_url=base_url,
        api_key=api_key,
        temperature=cfg.get("temperature", 0.1),
        max_tokens=cfg.get("max_tokens", 4096),
        timeout=timeout,
        disabled_params=disabled_params,
    )


def _get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = _create_llm()
    return _llm_instance


def _structured(schema: type[BaseModel]):
    """
    返回 with_structured_output 链。

    method 由 config.llm.structured_output_method 控制：
      "function_calling" — 默认，兼容 Ollama/LiteLLM 等
      "json_schema"      — OpenAI 原生，strict 模式，精度更高
    """
    from tuneai.config import get_llm_config
    method = get_llm_config().get("structured_output_method", "function_calling")

    llm = _get_llm()
    if method == "json_schema":
        return llm.with_structured_output(schema, method="json_schema", strict=True)
    else:
        return llm.with_structured_output(schema, method="function_calling")


# ---------------------------------------------------------------------------
# 任务 A：调号 OCR 纠错
# ---------------------------------------------------------------------------

def correct_key_signature(
    raw_text: str,
    context: str,
    request_id: str,
) -> KeyCorrectionResult:
    """
    给定 OCR 识别到的原始文字，纠正调号格式。

    流程：
      1. 空输入 → 直接返回默认 1=C（不调用 LLM）
      2. LLM structured output → KeyCorrectionResult
      3. LLM 失败 → 正则回退解析 _fallback_key_parse
    """
    log = get_logger("llm")

    if not raw_text:
        log.warning("correct_key_signature: OCR 未识别到调号，默认 1=C")
        return KeyCorrectionResult(tonic="C", label="1=C", confidence=0.3, notes="OCR未识别到调号")

    prompt = (
        "你是简谱（数字谱）专家。以下是 OCR 识别到的调号文字，可能含有识别错误。\n\n"
        f"原始文字: {raw_text!r}\n"
        f"上下文: {context}\n\n"
        "请纠正并提取正确的调号信息。\n"
        "调号格式为 '1=X'，其中 X 是主音（C D E F G A B，可带 # 或 b）。\n"
        "常见 OCR 错误：= 识别为 ＝ 或 一；# 识别为 井；b 识别为 6 或 B。"
    )

    try:
        result = _structured(KeyCorrectionResult).invoke(prompt)
        log.debug(f"key correction: {raw_text!r} → {result.label} (conf={result.confidence:.2f})")
        return result
    except Exception as e:
        log.warning(f"LLM key correction failed ({type(e).__name__}: {e})，回退正则解析")
        return _fallback_key_parse(raw_text)


# ---------------------------------------------------------------------------
# 任务 B：低置信度小节补全
# ---------------------------------------------------------------------------

def correct_low_confidence_measure(
    measure_tokens: list[dict],
    image_region_b64: str,
    active_key: str,
    request_id: str,
) -> MeasureCorrectionResult:
    """
    给定低置信度 OCR token 列表，补全或纠正音符解析。

    失败时原样返回 measure_tokens，confidence=0.5，不向外抛出。
    """
    log = get_logger("llm")

    tokens_str = json.dumps(measure_tokens, ensure_ascii=False, indent=2)
    prompt = (
        "你是简谱（数字谱）专家。以下是一个小节的 OCR 识别结果（含置信度）：\n\n"
        f"当前调号: 1={active_key}\n"
        f"OCR Token 列表:\n{tokens_str}\n\n"
        "请分析并纠正其中低置信度（confidence < 0.7）的音符。\n"
        "返回完整的事件列表，每个事件包含字段：id, type, degree, accidental, octave_shift。\n"
        "如无需修改，原样返回，confidence 设为 1.0。"
    )

    try:
        result = _structured(MeasureCorrectionResult).invoke(prompt)
        log.debug(f"measure correction: {len(measure_tokens)} tokens → conf={result.confidence:.2f}")
        return result
    except Exception as e:
        log.warning(f"LLM measure correction failed ({type(e).__name__}: {e})")
        return MeasureCorrectionResult(
            events=measure_tokens,
            confidence=0.5,
            notes=f"LLM调用失败: {type(e).__name__}: {e}",
        )


# ---------------------------------------------------------------------------
# 正则回退（LLM 不可用时）
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r"1\s*[=＝一]\s*([A-G][#b♯♭]?)")

def _fallback_key_parse(raw_text: str) -> KeyCorrectionResult:
    """
    正则解析调号，作为 LLM 不可用时的降级方案。
    支持全角等号、Unicode 升降号等常见 OCR 变形。
    """
    m = _KEY_RE.search(raw_text)
    if m:
        tonic = m.group(1).replace("♯", "#").replace("♭", "b")
        return KeyCorrectionResult(
            tonic=tonic,
            label=f"1={tonic}",
            confidence=0.6,
            notes="LLM不可用，正则回退解析",
        )
    return KeyCorrectionResult(tonic="C", label="1=C", confidence=0.2, notes="正则无法解析，回退默认调 C")
