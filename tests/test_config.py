import os
from unittest.mock import patch, MagicMock
from notesculpt.config import ConfigLoader
from notesculpt.errors import ConfigError


class TestConfigLoaderLoad:
    def test_load_from_keyring(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.return_value = "sk-keyring-key"
            with patch("os.environ", {}):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.api_key == "sk-keyring-key"

    def test_load_falls_back_to_env(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "sk-env-key"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.api_key == "sk-env-key"

    def test_load_falls_back_to_dotenv(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={"DEEPSEEK_API_KEY": "sk-dotenv-key"}):
                    config = loader.load()
        assert config.api_key == "sk-dotenv-key"

    def test_load_raises_when_no_key(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    try:
                        loader.load()
                        assert False, "应该抛出 ConfigError"
                    except ConfigError as e:
                        assert "API Key" in str(e)

    def test_load_resolves_base_url(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-test" if k == "deepseek_api_key" else None
            with patch.dict("os.environ", {"DEEPSEEK_BASE_URL": "https://custom.api.com"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.base_url == "https://custom.api.com"

    def test_load_resolves_model(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-test" if k == "deepseek_api_key" else None
            with patch.dict("os.environ", {"DEEPSEEK_MODEL": "deepseek-reasoner"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.model == "deepseek-reasoner"

    def test_load_uses_defaults(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-test" if k == "deepseek_api_key" else None
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.base_url == "https://api.deepseek.com/v1"
        assert config.model == "deepseek-chat"


class TestConfigLoaderKeyManagement:
    def test_set_key(self):
        loader = ConfigLoader()
        with patch("keyring.set_password") as mock_set:
            loader.set_key("sk-new-key")
        mock_set.assert_called_once_with("notesculpt", "api_key", "sk-new-key")

    def test_delete_key(self):
        loader = ConfigLoader()
        with patch("keyring.delete_password") as mock_delete:
            loader.delete_key()
        mock_delete.assert_called_once_with("notesculpt", "api_key")


class TestConfigLoaderGetStatus:
    def test_status_key_configured(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value="sk-test"):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert status["key_configured"] is True

    def test_status_key_not_configured(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert status["key_configured"] is False

    def test_status_shows_model_and_url(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-test" if k == "api_key" else None
            with patch.dict("os.environ", {"DEEPSEEK_MODEL": "deepseek-reasoner"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert status["model"] == "deepseek-reasoner"
        assert status["base_url"] == "https://api.deepseek.com/v1"

    def test_status_does_not_leak_key(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-secret-123" if k == "deepseek_api_key" else None
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert "sk-secret-123" not in str(status)
        assert "api_key" not in status