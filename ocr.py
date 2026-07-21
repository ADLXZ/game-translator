import easyocr


class OCRReader:
    def __init__(self):
        self.reader = easyocr.Reader(["en"], gpu=False)

    def read_text(self, image_path):
        results = self.reader.readtext(image_path, detail=0)

        return results

