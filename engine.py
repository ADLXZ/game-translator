from collections import OrderedDict
from threading import Lock

from ocr import OCRReader
from screenshot import ScreenCapture
from translator import TextTranslator


class TranslationEngine:
    """Shared capture/OCR/translation services for all translation regions."""

    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.ocr_reader = OCRReader()
        self.text_translator = TextTranslator()

        # EasyOCR/PyTorch objects are shared by every region. Serializing access
        # prevents simultaneous workers from corrupting or mixing OCR results.
        self._processing_lock = Lock()

        self._translation_cache = OrderedDict()
        self._cache_limit = 500

    def capture_screen(self, region):
        return self.screen_capture.capture(region)

    def translate_screenshot(self, screenshot):
        with self._processing_lock:
            original_text = self.ocr_reader.read_text(screenshot)

            if not original_text:
                return "", ""

            translated_text = self._get_cached_translation(original_text)
            return original_text, translated_text

    def translate_screen(self, region):
        screenshot = self.capture_screen(region)
        return self.translate_screenshot(screenshot)

    def _get_cached_translation(self, text):
        cached = self._translation_cache.get(text)
        if cached is not None:
            self._translation_cache.move_to_end(text)
            return cached

        translated = self.text_translator.translate(text)
        self._translation_cache[text] = translated
        self._translation_cache.move_to_end(text)

        while len(self._translation_cache) > self._cache_limit:
            self._translation_cache.popitem(last=False)

        return translated
