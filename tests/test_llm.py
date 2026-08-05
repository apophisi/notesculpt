import pytest
from unittest.mock import patch, MagicMock
from notesculpt.llm import LLMClient
from notesculpt.models import Config
from notesculpt.errors import (
    AuthError,
    RateLimitError,
    NetworkError,
    ServerError,
    FatalError,
)


@pytest.fixture
def config():
    return Config(api_key="sk-test")


@pytest.fixture
def mock_openai():
    with patch("notesculpt.llm.OpenAI") as mock:
        yield mock


class TestLLMClientRefine:
    def test_refine_returns_content(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# Refined content"
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        result = client.refine("system prompt", "user content")

        assert result == "# Refined content"
        mock_instance.chat.completions.create.assert_called_once()

    def test_refine_passes_correct_params(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "result"
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        client.refine("system prompt", "user content")

        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "deepseek-chat"
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][0]["content"] == "system prompt"
        assert call_kwargs["messages"][1]["role"] == "user"
        assert call_kwargs["messages"][1]["content"] == "user content"

    def test_refine_raises_when_content_empty(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        with pytest.raises(FatalError, match="空结果"):
            client.refine("system prompt", "user content")

    def test_refine_raises_when_content_none(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        with pytest.raises(FatalError, match="空结果"):
            client.refine("system prompt", "user content")


class TestLLMClientRetry:
    def test_retries_on_rate_limit(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep") as mock_sleep:
            result = client.refine("system", "user")

        assert result == "ok"
        assert mock_instance.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2

    def test_retries_on_network_error(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            openai.APIConnectionError(request=MagicMock()),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep"):
            result = client.refine("system", "user")

        assert result == "ok"
        assert mock_instance.chat.completions.create.call_count == 2

    def test_retries_on_server_error(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_instance.chat.completions.create.side_effect = [
            openai.APIStatusError("server error", response=mock_response, body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep"):
            result = client.refine("system", "user")

        assert result == "ok"
        assert mock_instance.chat.completions.create.call_count == 2

    def test_raises_immediately_on_auth_error(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_instance.chat.completions.create.side_effect = openai.AuthenticationError(
            "invalid key", response=mock_response, body=None
        )

        client = LLMClient(config)
        with pytest.raises(AuthError):
            client.refine("system", "user")
        assert mock_instance.chat.completions.create.call_count == 1

    def test_raises_after_exhausting_retries(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = openai.RateLimitError(
            "rate limited", response=MagicMock(), body=None
        )

        client = LLMClient(config)
        with patch("time.sleep"):
            with pytest.raises(RateLimitError):
                client.refine("system", "user")
        assert mock_instance.chat.completions.create.call_count == 3

    def test_retry_delays_follow_exponential_backoff(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep") as mock_sleep:
            client.refine("system", "user")

        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1, 2]