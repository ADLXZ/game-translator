from deep_translator import GoogleTranslator


class TextTranslator:
    def __init__(self, source="auto", target="zh-CN"):
        self.source = source
        self.target = target

    def translate(self, text):
        text = text.strip()
        if not text:
            return ""

        # Create a translator per request. This avoids sharing mutable network
        # client state between worker threads.
        return GoogleTranslator(
            source=self.source,
            target=self.target,
        ).translate(text)
