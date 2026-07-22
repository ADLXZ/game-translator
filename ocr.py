import re

import easyocr
import numpy as np
from PIL import Image


class OCRReader:
    """EasyOCR wrapper with conservative filtering to reduce false text."""

    def __init__(self, languages=None, gpu=False, minimum_confidence=0.50):
        self.languages = languages or ["en"]
        self.minimum_confidence = minimum_confidence
        self.reader = easyocr.Reader(self.languages, gpu=gpu)

    def read_text(self, image):
        if isinstance(image, Image.Image):
            image = np.asarray(image)

        results = self.reader.readtext(
            image,
            detail=1,
            paragraph=False,
            decoder="greedy",
            text_threshold=0.70,
            low_text=0.40,
            link_threshold=0.40,
            contrast_ths=0.10,
            adjust_contrast=0.50,
        )

        accepted_lines = []

        for _box, raw_text, confidence in results:
            text = self._clean_text(raw_text)

            if not self._is_reliable(text, float(confidence)):
                continue

            if accepted_lines and accepted_lines[-1] == text:
                continue

            accepted_lines.append(text)

        return "\n".join(accepted_lines).strip()

    def _is_reliable(self, text, confidence):
        if confidence < self.minimum_confidence:
            return False

        if not text:
            return False

        if not any(character.isalnum() for character in text):
            return False

        # Single-character OCR is a common false positive. Keep it only when
        # EasyOCR is highly confident.
        if len(text) == 1 and confidence < 0.85:
            return False

        # Reject strings that are mostly repeated punctuation/noise.
        alphanumeric_count = sum(character.isalnum() for character in text)
        if alphanumeric_count / max(1, len(text)) < 0.25:
            return False

        return True

    @staticmethod
    def _clean_text(text):
        text = str(text).replace("\u200b", " ")
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()
