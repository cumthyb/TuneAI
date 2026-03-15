"""
行切分、小节定位、候选符号框。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import cv2


@dataclass
class LineRegion:
    y_start: int
    y_end: int
    x_start: int
    x_end: int

    @property
    def height(self) -> int:
        return self.y_end - self.y_start

    @property
    def width(self) -> int:
        return self.x_end - self.x_start


@dataclass
class BBox:
    x: int
    y: int
    w: int
    h: int


def detect_lines(binary_img: np.ndarray) -> list[LineRegion]:
    """
    水平投影分析：统计每行黑像素数量，在投影的低谷处切分出乐谱行。
    """
    inv = cv2.bitwise_not(binary_img)  # 黑字变白
    h, w = inv.shape

    # 水平投影
    row_sums = np.sum(inv > 0, axis=1)
    # 归一化
    threshold = w * 0.02  # 一行中至少有 2% 的列有内容才算文字行

    in_line = False
    line_start = 0
    lines: list[LineRegion] = []
    min_line_height = max(10, h // 50)

    for y, s in enumerate(row_sums):
        if not in_line and s > threshold:
            in_line = True
            line_start = y
        elif in_line and s <= threshold:
            in_line = False
            if (y - line_start) >= min_line_height:
                lines.append(LineRegion(
                    y_start=max(0, line_start - 2),
                    y_end=min(h, y + 2),
                    x_start=0,
                    x_end=w,
                ))
    if in_line and (h - line_start) >= min_line_height:
        lines.append(LineRegion(y_start=max(0, line_start - 2), y_end=h, x_start=0, x_end=w))

    return lines


def detect_barlines(binary_img: np.ndarray, line: LineRegion) -> list[int]:
    """
    垂直投影分析：在行区域内找竖线（小节线），返回 x 坐标列表。
    """
    region = binary_img[line.y_start:line.y_end, line.x_start:line.x_end]
    inv = cv2.bitwise_not(region)
    col_sums = np.sum(inv > 0, axis=0)

    line_h = line.height
    # 竖线：列中大部分行都是黑色
    threshold = line_h * 0.7
    barline_xs: list[int] = []
    prev_above = False

    for x, s in enumerate(col_sums):
        above = s >= threshold
        if above and not prev_above:
            barline_xs.append(x + line.x_start)
        prev_above = above

    return barline_xs


def extract_symbol_candidates(binary_img: np.ndarray, line: LineRegion) -> list[BBox]:
    """
    连通域分析：在行区域内找所有候选符号框，过滤噪点。
    """
    region = binary_img[line.y_start:line.y_end, line.x_start:line.x_end]
    inv = cv2.bitwise_not(region)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inv, connectivity=8)

    candidates: list[BBox] = []
    min_area = 4
    max_area = region.shape[0] * region.shape[1] // 2

    for i in range(1, num_labels):  # skip background (0)
        x, y, w, h, area = stats[i]
        if min_area <= area <= max_area:
            candidates.append(BBox(
                x=x + line.x_start,
                y=y + line.y_start,
                w=w,
                h=h,
            ))

    return candidates
