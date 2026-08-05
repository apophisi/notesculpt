import os
import keyring
from dotenv import dotenv_values
from notesculpt.models import Config
from notesculpt.errors import ConfigError


class ConfigLoader:
    KEYRING_SERVICE = "notesculpt"
    KEYRING_KEY = "api_key"

    def __init__(self):
        self._dotenv = None

    def load(self) -> Config:
        api_key = self._resolve("DEEPSEEK_API_KEY")
        if not api_key:
            raise ConfigError("未找到 API Key。请运行: notesculpt config set-key")
        base_url = self._resolve("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1"
        model = self._resolve("DEEPSEEK_MODEL") or "deepseek-chat"
        return Config(api_key=api_key, base_url=base_url, model=model)

    def _resolve(self, key: str) -> str | None:
        value = keyring.get_password(self.KEYRING_SERVICE, key.lower())
        if value:
            return value
        value = os.environ.get(key)
        if value:
            return value
        if self._dotenv is None:
            self._dotenv = dotenv_values(".env")
        return self._dotenv.get(key)

    def set_key(self, api_key: str) -> None:
        keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_KEY, api_key)

    def delete_key(self) -> None:
        keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_KEY)

    def get_status(self) -> dict:
        has_key = bool(self._resolve("DEEPSEEK_API_KEY"))
        return {
            "key_configured": has_key,
            "model": self._resolve("DEEPSEEK_MODEL") or "deepseek-chat",
            "base_url": self._resolve("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1",
        }