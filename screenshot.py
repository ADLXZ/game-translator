from mss import mss


class ScreenCapture:

    def capture(self):
        with mss() as sct:
            filename = sct.shot(output="screenshots/screenshot.png")

        print(f"Screenshot saved to: {filename}")


