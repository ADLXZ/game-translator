import easyocr
import numpy as np
from PIL import Image


class OCRReader:
    def __init__(self):
        self.reader = easyocr.Reader(
            ["en"],
            gpu=False,
        )

    def read_text(self, image):
        if isinstance(image, Image.Image):
            image = np.array(image)

        results = self.reader.readtext(
            image,
            detail=0,
        )

        text = "\n".join(results).strip()

        return text


