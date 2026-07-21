from pathlib import Path

from mss import mss
from mss.tools import to_png


class ScreenCapture:
    def __init__(self):
        self.output_path = Path("screenshots/screenshot.png")

    def capture(self, region=None):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with mss() as sct:
            if region is None:
                filename = sct.shot(output=str(self.output_path))
            else:
                screenshot = sct.grab(region)

                to_png(
                    screenshot.rgb,
                    screenshot.size,
                    output=str(self.output_path),
                )

                filename = str(self.output_path)

        print(f"Screenshot saved to: {filename}")

        return filename


