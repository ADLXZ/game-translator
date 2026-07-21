from screenshot import ScreenCapture
from ocr import OCRReader
from translator import TextTranslator

class TranslationEngine:
    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.ocr_reader = OCRReader()
        self.text_translator = TextTranslator()

    def translate_screen(self):
        image_path = self.screen_capture.capture()

        detected_lines = self.ocr_reader.read_text(image_path)

        original_text = "\n".join(detected_lines)

        translated_text = self.text_translator.translate(original_text)

        return translated_text





