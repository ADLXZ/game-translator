import mss
import mss.tools

with mss.MSS() as sct:

    monitor = sct.monitors[1]

    screenshot = sct.grab(monitor)

    mss.tools.to_png(
        screenshot.rgb,
        screenshot.size,
        output="screenshot.png"
    )

print("截图成功！")


