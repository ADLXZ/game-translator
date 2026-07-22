from mss import mss
from PIL import Image


class ScreenCapture:
    def capture(self, region=None):
        with mss() as screen_capture:
            if region is None:
                monitor = screen_capture.monitors[1]
            else:
                monitor = {
                    "left": int(region["left"]),
                    "top": int(region["top"]),
                    "width": max(1, int(region["width"])),
                    "height": max(1, int(region["height"])),
                }

            screenshot = screen_capture.grab(monitor)

            return Image.frombytes(
                "RGB",
                screenshot.size,
                screenshot.rgb,
            )
