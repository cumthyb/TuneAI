"""
图像预处理（第一步，本地）：灰度化 → 去噪 → 倾斜校正（deskew）。
输出干净的灰度图，供 Qwen-VL 和阿里 OCR 使用。
"""
from __future__ import annotations

import numpy as np
import cv2


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    解码图像字节 → 灰度化 → 去噪 → 倾斜校正。
    返回灰度 numpy 数组（uint8）。
    """
    nparr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图像，请检查文件格式")

    # 灰度化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 去噪
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # 倾斜校正
    return _deskew(denoised)


def _deskew(gray: np.ndarray) -> np.ndarray:
    """利用 Hough 变换估算倾斜角度并旋转校正。"""
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
    )
    edges = cv2.Canny(cv2.bitwise_not(binary), 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
    if lines is None or len(lines) == 0:
        return gray

    angles = []
    for line in lines[:20]:
        rho, theta = line[0]
        angle = np.degrees(theta) - 90
        if abs(angle) < 10:
            angles.append(angle)

    if not angles:
        return gray

    median_angle = float(np.median(angles))
    if abs(median_angle) < 0.5:
        return gray

    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    return cv2.warpAffine(
        gray, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
