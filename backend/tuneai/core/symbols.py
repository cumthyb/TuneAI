"""
OpenCV 八度点、时值线、小节线、几何关系。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import cv2

from tuneai.core.layout import LineRegion


@dataclass
class OctaveDot:
    x: int
    y: int
    position: Literal["above", "below"]


@dataclass
class DurationMark:
    type: Literal["dash", "underline"]
    bbox: list[int]   # [x, y, w, h]


def detect_octave_dots(binary_img: np.ndarray, line_region: LineRegion) -> list[OctaveDot]:
    """
    在行区域内寻找小连通域（八度点）。
    位于行中线上方 → above，下方 → below。
    """
    region = binary_img[line_region.y_start:line_region.y_end,
                         line_region.x_start:line_region.x_end]
    inv = cv2.bitwise_not(region)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inv, connectivity=8)

    line_mid_y = (line_region.y_end + line_region.y_start) // 2
    # Typical dot area: small square
    min_area, max_area = 2, 30

    dots: list[OctaveDot] = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        if min_area <= area <= max_area and w <= 8 and h <= 8:
            abs_y = y + line_region.y_start
            cx = x + line_region.x_start + w // 2
            cy = abs_y + h // 2
            position: Literal["above", "below"] = "above" if cy < line_mid_y else "below"
            dots.append(OctaveDot(x=cx, y=cy, position=position))

    return dots


def detect_duration_marks(binary_img: np.ndarray, line_region: LineRegion) -> list[DurationMark]:
    """
    在行区域内寻找横线：
    - 较短横线（相对字符宽）= underline（下划线，音符加时值）
    - 较长横线（超出单字符宽很多）= dash（延音线）
    """
    region = binary_img[line_region.y_start:line_region.y_end,
                         line_region.x_start:line_region.x_end]
    inv = cv2.bitwise_not(region)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inv, connectivity=8)

    marks: list[DurationMark] = []
    # 预估字符宽度（行高约等于字符高度）
    char_w_est = max(10, line_region.height)

    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        # 横线：宽 >> 高，高度很小
        if w >= char_w_est * 0.6 and h <= max(3, line_region.height // 8):
            mark_type: Literal["dash", "underline"] = (
                "dash" if w >= char_w_est * 1.5 else "underline"
            )
            abs_x = x + line_region.x_start
            abs_y = y + line_region.y_start
            marks.append(DurationMark(type=mark_type, bbox=[abs_x, abs_y, w, h]))

    return marks


def detect_accidentals(binary_img: np.ndarray, line_region: LineRegion) -> list[dict]:
    """
    在行区域内检测升降号（# 和 b）。
    使用形态学分析：升号（#）水平线+垂直线交叉；降号（b）曲线。
    返回 dict: {"type": "sharp"|"flat", "bbox": [x,y,w,h]}
    """
    region = binary_img[line_region.y_start:line_region.y_end,
                         line_region.x_start:line_region.x_end]
    inv = cv2.bitwise_not(region)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inv, connectivity=8)

    accidentals: list[dict] = []
    char_h_est = max(10, line_region.height)

    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        # 升降号通常比单个数字小，但有一定面积
        if not (char_h_est * 0.3 <= h <= char_h_est * 1.2):
            continue
        if area < 20:
            continue

        # 提取连通域图像块
        mask = (labels[y:y+h, x:x+w] == i).astype(np.uint8) * 255

        # 粗略判断：升号 (#) 的宽高比接近 1，降号 (b) 较高（h > w）
        aspect = h / max(w, 1)

        abs_x = x + line_region.x_start
        abs_y = y + line_region.y_start

        if aspect > 1.5:
            # 更高 → 可能是 b (flat)
            accidentals.append({"type": "flat", "bbox": [abs_x, abs_y, w, h]})
        elif 0.6 <= aspect <= 1.4 and w >= char_h_est * 0.2:
            # 方形 → 可能是 # (sharp)
            accidentals.append({"type": "sharp", "bbox": [abs_x, abs_y, w, h]})

    return accidentals
