from screenshot import ScreenCapture
from ocr import OCRReader
from translator import TextTranslator

class TranslationEngine:
    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.ocr_reader = OCRReader()
        self.text_translator = TextTranslator()

    def capture_screen(self, region):
        return self.screen_capture.capture(region)

    def translate_screenshot(self, screenshot):
        original_text = self.ocr_reader.read_text(
            screenshot
        )

        if not original_text:
            return "", ""

        translated_text = self.text_translator.translate(
            original_text
        )

        return original_text, translated_text

    def translate_screen(self, region):
        screenshot = self.capture_screen(region)

        return self.translate_screenshot(
            screenshot
        )




















