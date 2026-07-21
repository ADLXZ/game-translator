from deep_translator import GoogleTranslator


class TextTranslator:
    def __init__(self):
        self.translator = GoogleTranslator(
            source="auto",
            target="zh-CN",
        )

    def translate(self, text):
        if not text.strip():
            return ""

        translated_text = self.translator.translate(text)

        return translated_text



if __name__ == "__main__":
    translator = TextTranslator()

    result = translator.translate(
        "Start a new game and continue your adventure."
    )

    print(result)





