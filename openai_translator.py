from __future__ import annotations


from openai import OpenAI




class OpenAITranslator:
    """Use the OpenAI API to translate game dialogue."""


    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        style: str = "Natural",
        timeout_seconds: float = 30.0,
    ) -> None:
        api_key = api_key.strip()
        model = model.strip()
        style = style.strip()


        if not api_key:
            raise ValueError(
                "OpenAI API key is required."
            )


        if not model:
            raise ValueError(
                "OpenAI model is required."
            )


        self.client = OpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=1,
        )


        self.model = model
        self.style = style or "Natural"


    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: str = "",
    ) -> str:
        cleaned_text = text.strip()


        if not cleaned_text:
            return ""


        response = self.client.responses.create(
            model=self.model,
            instructions=self._build_instructions(
                source_language=source_language,
                target_language=target_language,
            ),
            input=self._build_input(
                text=cleaned_text,
                context=context,
            ),


            # Translation generally does not require
            # deep reasoning.
            reasoning={
                "effort": "minimal",
            },


            # Game dialogue should normally be short.
            max_output_tokens=300,
        )


        translated_text = (
            response.output_text or ""
        ).strip()


        if not translated_text:
            raise RuntimeError(
                "OpenAI returned an empty translation."
            )


        return translated_text


    def _build_instructions(
        self,
        source_language: str,
        target_language: str,
    ) -> str:
        style_instruction = (
            self._get_style_instruction()
        )


        return (
            f"Translate game dialogue from "
            f"{source_language} to {target_language}.\n"
            f"Style: {style_instruction}\n"
            "Preserve meaning, emotion, politeness, "
            "character voice, and useful line breaks.\n"
            "Correct only obvious OCR spacing or "
            "punctuation errors.\n"
            "Do not invent missing text.\n"
            "Context is reference only; translate only "
            "the newest OCR text.\n"
            "Return translated text only."
        )


    @staticmethod
    def _build_input(
        text: str,
        context: str,
    ) -> str:
        cleaned_context = context.strip()


        if not cleaned_context:
            return text


        return (
            f"Context:\n{cleaned_context}\n\n"
            f"Text:\n{text}"
        )


    def _get_style_instruction(self) -> str:
        styles = {
            "Natural": (
                "Fluent and natural game dialogue."
            ),
            "Literal": (
                "Stay close to the original wording."
            ),
            "Visual Novel": (
                "Polished visual-novel dialogue with "
                "emotional nuance."
            ),
            "Casual Dialogue": (
                "Conversational and informal when appropriate."
            ),
            "Fantasy RPG": (
                "Preserve fantasy terminology, titles, "
                "roles, and dramatic tone."
            ),
            "Formal": (
                "Polished, respectful, formal language."
            ),
        }


        return styles.get(
            self.style,
            styles["Natural"],
        )



