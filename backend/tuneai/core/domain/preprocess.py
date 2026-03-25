from __future__ import annotations

import cv2
import numpy as np
from typing import Protocol


class PreprocessingStrategy(Protocol):
    """图像预处理策略协议。"""

    def process(self, img: np.ndarray) -> np.ndarray:
        """输入 BGR image ndarray，输出处理后的灰度 ndarray。"""
        ...


class SimplePreprocessor:
    """当前预处理逻辑：灰度 + 去噪 + 纠偏。"""

    def process(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        return self._deskew(denoised)

    def _deskew(self, gray: np.ndarray) -> np.ndarray:
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
        matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        return cv2.warpAffine(
            gray,
            matrix,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )


class OcrOptimizedPreprocessor:
    """针对 OCR 优化的预处理策略：分辨率归一化 + CLAHE + 自适应二值化 + 形态学清理。"""

    CANONICAL_HEIGHT = 800

    def process(self, img: np.ndarray) -> np.ndarray:
        # Step 1: 分辨率归一化
        img = self._normalize_size(img)

        # Step 2: 去噪
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

        # Step 3: CLAHE 对比度增强
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Step 4: 自适应二值化
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )

        # Step 5: 形态学操作去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Step 6: 纠偏
        return self._deskew(cleaned)

    def _normalize_size(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        if h > self.CANONICAL_HEIGHT:
            scale = self.CANONICAL_HEIGHT / h
            return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return img

    def _deskew(self, gray: np.ndarray) -> np.ndarray:
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
        matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        return cv2.warpAffine(
            gray,
            matrix,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图像，请检查文件格式")

    # 策略选择：基于分辨率
    h, w = img.shape[:2]
    if h < 300 or w < 300:
        return OcrOptimizedPreprocessor().process(img)
    return SimplePreprocessor().process(img)
