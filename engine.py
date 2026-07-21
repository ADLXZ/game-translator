from screenshot import ScreenCapture
from ocr import OCRReader


class TranslationEngine:
    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.ocr_reader = OCRReader()

    def translate_screen(self):
        image_path = self.screen_capture.capture()

        detected_text = self.ocr_reader.read_text(image_path)

        return detected_text


