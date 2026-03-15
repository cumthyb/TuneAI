"""
音高评估与迭代调整（Pipeline 第六步，本地 + 可选 LLM）。

两项检查（均在 validate 之后、render 之前执行）：

  检查 A  音高过高
    评估转调后音符的整体音域是否偏高（octave_shift 分布 + LLM 辅助判断）。
    若整体偏高，将所有音符降低一个八度（shift_octave(score, -1)）。

  检查 B  半音过多（临时记号密度高）
    统计非 natural 音符比例。比例超过阈值时，
    在目标调附近（±3 半音）枚举候选调，
    对每个候选调重新执行 transpose_score_ir，
    选取使半音数量最少的调作为新目标调。
    此为迭代过程：调整后再次检查 A，直至收敛或达到最大迭代次数。

  LLM 辅助
    检查 A/B 均可引入 LLM 作为辅助评估器（tuneai.core.llm.assess_pitch_range）。
    LLM 失败时退化为纯规则判断，不阻断流程。

MVP 实现
    两项检查均跳过，原样返回输入的 ScoreIR 和空 Warning 列表。
    接口与返回类型已固定，未来直接填充实现即可。
"""
from __future__ import annotations

from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import ScoreIR


def adjust_pitch(
    score: ScoreIR,
    request_id: str = "",
) -> tuple[ScoreIR, list[Warning]]:
    """
    对转调后的 ScoreIR 执行音高评估与迭代调整。

    Args:
        score:      transpose_score_ir 输出的 ScoreIR（已完成移调）
        request_id: 请求 ID，用于日志追踪

    Returns:
        (adjusted_score, warnings)
        - adjusted_score: 调整后的 ScoreIR（MVP 阶段与输入相同）
        - warnings:       调整过程中产生的 Warning 列表

    完整实现时的处理流程（TODO）：
        1. 检查 A：评估音高
           a. 统计 octave_shift 分布（均值、最大值）
           b. 可选：调用 llm.assess_pitch_range 获得 LLM 判断
           c. 若规则或 LLM 判定偏高，执行 music.shift_octave(score, -1)
              并记录 Warning(type="octave_adjusted", message="...")
        2. 检查 B：评估半音密度
           a. 调用 music.count_accidentals(score) 统计半音数
           b. 若比例超过阈值（如 30%），枚举候选调：
              KEY_TO_PC 中与当前 target_key 相差 ±3 半音以内的调名
           c. 对每个候选调调用 music.transpose_score_ir 并重新统计半音数
           d. 选半音最少的候选调作为新目标调，更新 score
              并记录 Warning(type="key_adjusted", message="...")
        3. 若检查 B 发生了调整，重新执行检查 A（最多 MAX_ITER=3 次）
    """
    log = get_logger("pitch_adjust")
    log.debug(f"[pitch_adjust] MVP stub, request_id={request_id!r}")
    return score, []
