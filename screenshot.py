from mss import mss
from PIL import Image


class ScreenCapture:
    def capture(self, region=None):
        with mss() as sct:
            if region is None:
                monitor = sct.monitors[1]
            else:
                monitor = region

            screenshot = sct.grab(monitor)

            image = Image.frombytes(
                "RGB",
                screenshot.size,
                screenshot.rgb,
            )

        return image


