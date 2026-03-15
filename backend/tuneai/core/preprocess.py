"""
图像归一化、增强、校正。
"""
from __future__ import annotations

import numpy as np
import cv2


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    解码图像字节 → 灰度化 → 去噪 → 二值化 → 倾斜校正 → 对比度增强 → 边缘裁切。
    返回二值化（黑字白底）numpy 数组。
    """
    # Decode
    nparr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图像，请检查文件格式")

    # 灰度化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 去噪
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # 二值化（自适应阈值）
    binary = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=8,
    )

    # 确保黑字白底（背景为白=255）
    if np.mean(binary) < 128:
        binary = cv2.bitwise_not(binary)

    # 倾斜校正（Hough 直线）
    binary = _deskew(binary)

    # 对比度增强（CLAHE on gray then re-threshold）
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    binary2 = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=8,
    )
    if np.mean(binary2) < 128:
        binary2 = cv2.bitwise_not(binary2)

    # 边缘裁切（去除大量空白边缘）
    binary2 = _crop_border(binary2)

    return binary2


def _deskew(binary: np.ndarray) -> np.ndarray:
    """利用 Hough 变换估算倾斜角度并旋转校正。"""
    edges = cv2.Canny(cv2.bitwise_not(binary), 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
    if lines is None or len(lines) == 0:
        return binary

    angles = []
    for line in lines[:20]:
        rho, theta = line[0]
        angle = np.degrees(theta) - 90
        if abs(angle) < 10:  # only consider near-horizontal lines
            angles.append(angle)

    if not angles:
        return binary

    median_angle = float(np.median(angles))
    if abs(median_angle) < 0.5:
        return binary

    h, w = binary.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_NEAREST,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    return rotated


def _crop_border(binary: np.ndarray, margin: int = 5) -> np.ndarray:
    """裁去几乎全白的边缘行/列，保留 margin 像素边距。"""
    inv = cv2.bitwise_not(binary)
    rows = np.any(inv > 0, axis=1)
    cols = np.any(inv > 0, axis=0)
    if not rows.any() or not cols.any():
        return binary
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    r0 = max(0, r0 - margin)
    r1 = min(binary.shape[0] - 1, r1 + margin)
    c0 = max(0, c0 - margin)
    c1 = min(binary.shape[1] - 1, c1 + margin)
    return binary[r0:r1 + 1, c0:c1 + 1]
