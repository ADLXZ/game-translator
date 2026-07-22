import hashlib
import random
from threading import Lock

import requests
from deep_translator import GoogleTranslator


class TextTranslator:
    """
    Translation service supporting Google and Baidu.

    Baidu credentials are stored only in memory.
    They disappear when the program closes.
    """

    SUPPORTED_PROVIDERS = {
        "google",
        "baidu",
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

        # The UI thread may update credentials while the translation
        # worker reads them, so protect the shared values.
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

    def translate(self, text):
        text = (text or "").strip()

        if not text:
            return ""

        with self._settings_lock:
            provider = self._provider
            baidu_app_id = self._baidu_app_id
            baidu_secret_key = (
                self._baidu_secret_key
            )

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

        raise RuntimeError(
            "Unknown translation provider: "
            f"{provider}"
        )

    def _translate_with_google(self, text):
        return GoogleTranslator(
            source=self.source,
            target=self.target,
        ).translate(text)

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


