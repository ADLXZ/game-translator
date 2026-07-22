from screenshot import ScreenCapture
from ocr import OCRReader
from translator import TextTranslator

class TranslationEngine:

    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.ocr_reader = OCRReader()
        self.text_translator = TextTranslator()

    def translate_screen(self, region=None):
        image_path = self.screen_capture.capture(region)

        detected_lines = self.ocr_reader.read_text(image_path)

        if not detected_lines:
            return ""

        original_text = "\n".join(detected_lines).strip()

        if not original_text:
            return ""

        translated_text = self.text_translator.translate(
            original_text
        )

        return translated_text











