from __future__ import annotations


import hashlib
import random
from threading import Lock


import requests
from deep_translator import GoogleTranslator


from openai_translator import OpenAITranslator




class TextTranslator:
    """
    Translation service supporting Google, Baidu, and OpenAI.


    Baidu and OpenAI credentials are stored only in memory.
    They disappear when the program closes.
    """


    SUPPORTED_PROVIDERS = {
        "google",
        "baidu",
        "openai",
    }


    SUPPORTED_OPENAI_STYLES = {
        "Natural",
        "Literal",
        "Visual Novel",
        "Casual Dialogue",
        "Fantasy RPG",
        "Formal",
    }


    def __init__(
        self,
        source="auto",
        target="zh-CN",
        provider="google",
    ):
        self.source = source
        self.target = target


        self._provider = "google"


        self._baidu_app_id = ""
        self._baidu_secret_key = ""


        self._openai_api_key = ""
        self._openai_model = "gpt-5-mini"
        self._openai_style = "Natural"


        # The UI thread may update credentials while a translation
        # worker reads them, so protect all shared settings.
        self._settings_lock = Lock()


        self.set_provider(provider)


    @property
    def provider(self):
        with self._settings_lock:
            return self._provider


    def set_provider(self, provider):
        normalized_provider = (
            str(provider)
            .strip()
            .lower()
        )


        if (
            normalized_provider
            not in self.SUPPORTED_PROVIDERS
        ):
            raise ValueError(
                "Unsupported translation provider: "
                f"{provider}"
            )


        with self._settings_lock:
            self._provider = normalized_provider


    # ---------------------------------------------------------
    # Baidu configuration
    # ---------------------------------------------------------


    def set_baidu_credentials(
        self,
        app_id,
        secret_key,
    ):
        app_id = (app_id or "").strip()
        secret_key = (secret_key or "").strip()


        if not app_id:
            raise ValueError(
                "Baidu APP ID cannot be empty."
            )


        if not secret_key:
            raise ValueError(
                "Baidu Secret Key cannot be empty."
            )


        with self._settings_lock:
            self._baidu_app_id = app_id
            self._baidu_secret_key = secret_key


    def has_baidu_credentials(self):
        with self._settings_lock:
            return bool(
                self._baidu_app_id
                and self._baidu_secret_key
            )


    def clear_baidu_credentials(self):
        with self._settings_lock:
            self._baidu_app_id = ""
            self._baidu_secret_key = ""


    # ---------------------------------------------------------
    # OpenAI configuration
    # ---------------------------------------------------------


    def set_openai_configuration(
        self,
        api_key,
        model="gpt-5-mini",
        style="Natural",
    ):
        api_key = (api_key or "").strip()
        model = (model or "").strip()
        style = (style or "").strip()


        if not api_key:
            raise ValueError(
                "OpenAI API key cannot be empty."
            )


        if not model:
            raise ValueError(
                "OpenAI model cannot be empty."
            )


        if style not in self.SUPPORTED_OPENAI_STYLES:
            raise ValueError(
                "Unsupported OpenAI translation style: "
                f"{style}"
            )


        with self._settings_lock:
            self._openai_api_key = api_key
            self._openai_model = model
            self._openai_style = style


    def has_openai_configuration(self):
        with self._settings_lock:
            return bool(
                self._openai_api_key
                and self._openai_model
            )


    def clear_openai_configuration(self):
        with self._settings_lock:
            self._openai_api_key = ""
            self._openai_model = "gpt-5-mini"
            self._openai_style = "Natural"


    # ---------------------------------------------------------
    # Translation entry point
    # ---------------------------------------------------------


    def translate(
        self,
        text,
        context="",
    ):
        text = (text or "").strip()
        context = (context or "").strip()


        if not text:
            return ""


        # Copy the settings while holding the lock, then release it
        # before performing any network request.
        with self._settings_lock:
            provider = self._provider


            baidu_app_id = self._baidu_app_id
            baidu_secret_key = (
                self._baidu_secret_key
            )


            openai_api_key = self._openai_api_key
            openai_model = self._openai_model
            openai_style = self._openai_style


        if provider == "google":
            return self._translate_with_google(
                text
            )


        if provider == "baidu":
            return self._translate_with_baidu(
                text=text,
                app_id=baidu_app_id,
                secret_key=baidu_secret_key,
            )


        if provider == "openai":
            return self._translate_with_openai(
                text=text,
                context=context,
                api_key=openai_api_key,
                model=openai_model,
                style=openai_style,
            )


        raise RuntimeError(
            "Unknown translation provider: "
            f"{provider}"
        )


    # ---------------------------------------------------------
    # Google
    # ---------------------------------------------------------


    def _translate_with_google(
        self,
        text,
    ):
        return GoogleTranslator(
            source=self.source,
            target=self.target,
        ).translate(text)


    # ---------------------------------------------------------
    # OpenAI
    # ---------------------------------------------------------


    def _translate_with_openai(
        self,
        text,
        context,
        api_key,
        model,
        style,
    ):
        if not api_key:
            raise RuntimeError(
                "OpenAI API key has not been "
                "configured in the main menu."
            )


        translator = OpenAITranslator(
            api_key=api_key,
            model=model,
            style=style,
        )


        source_language = (
            self._get_openai_source_language()
        )


        target_language = (
            self._get_openai_target_language()
        )


        return translator.translate(
            text=text,
            source_language=source_language,
            target_language=target_language,
            context=context,
        )


    def _get_openai_source_language(self):
        language = str(
            self.source
        ).strip().lower()


        language_map = {
            "auto": "the automatically detected language",
            "en": "English",
            "english": "English",
            "zh": "Chinese",
            "zh-cn": "Simplified Chinese",
            "zh-tw": "Traditional Chinese",
            "chinese": "Chinese",
            "ja": "Japanese",
            "jp": "Japanese",
            "japanese": "Japanese",
            "ko": "Korean",
            "kor": "Korean",
            "korean": "Korean",
            "fr": "French",
            "french": "French",
            "de": "German",
            "german": "German",
            "es": "Spanish",
            "spanish": "Spanish",
            "ru": "Russian",
            "russian": "Russian",
        }


        return language_map.get(
            language,
            self.source,
        )


    def _get_openai_target_language(self):
        language = str(
            self.target
        ).strip().lower()


        language_map = {
            "zh": "Simplified Chinese",
            "zh-cn": "Simplified Chinese",
            "zh-tw": "Traditional Chinese",
            "chinese": "Simplified Chinese",
            "en": "English",
            "english": "English",
            "ja": "Japanese",
            "jp": "Japanese",
            "japanese": "Japanese",
            "ko": "Korean",
            "kor": "Korean",
            "korean": "Korean",
            "fr": "French",
            "french": "French",
            "de": "German",
            "german": "German",
            "es": "Spanish",
            "spanish": "Spanish",
            "ru": "Russian",
            "russian": "Russian",
        }


        return language_map.get(
            language,
            self.target,
        )


    # ---------------------------------------------------------
    # Baidu
    # ---------------------------------------------------------


    def _translate_with_baidu(
        self,
        text,
        app_id,
        secret_key,
    ):
        if not app_id or not secret_key:
            raise RuntimeError(
                "Baidu credentials have not been "
                "configured in the main menu."
            )


        salt = str(
            random.randint(
                32768,
                65536,
            )
        )


        source_language = (
            self._get_baidu_source_language()
        )


        target_language = (
            self._get_baidu_target_language()
        )


        sign_source = (
            app_id
            + text
            + salt
            + secret_key
        )


        sign = hashlib.md5(
            sign_source.encode("utf-8")
        ).hexdigest()


        response = requests.post(
            "https://fanyi-api.baidu.com/"
            "api/trans/vip/translate",
            data={
                "q": text,
                "from": source_language,
                "to": target_language,
                "appid": app_id,
                "salt": salt,
                "sign": sign,
            },
            timeout=15,
        )


        response.raise_for_status()


        result = response.json()


        if "error_code" in result:
            error_code = result.get(
                "error_code",
                "unknown",
            )


            error_message = result.get(
                "error_msg",
                "Unknown Baidu Translate error",
            )


            raise RuntimeError(
                "Baidu Translate error "
                f"{error_code}: {error_message}"
            )


        translation_results = result.get(
            "trans_result",
            [],
        )


        if not translation_results:
            return ""


        translated_lines = [
            item.get("dst", "")
            for item in translation_results
            if item.get("dst")
        ]


        return "\n".join(
            translated_lines
        )


    def _get_baidu_source_language(self):
        language = self.source.lower()


        language_map = {
            "auto": "auto",
            "en": "en",
            "english": "en",
            "zh": "zh",
            "zh-cn": "zh",
            "chinese": "zh",
            "ja": "jp",
            "japanese": "jp",
            "ko": "kor",
            "korean": "kor",
        }


        return language_map.get(
            language,
            language,
        )


    def _get_baidu_target_language(self):
        language = self.target.lower()


        language_map = {
            "zh": "zh",
            "zh-cn": "zh",
            "chinese": "zh",
            "en": "en",
            "english": "en",
            "ja": "jp",
            "japanese": "jp",
            "ko": "kor",
            "korean": "kor",
        }


        return language_map.get(
            language,
            language,
        )



