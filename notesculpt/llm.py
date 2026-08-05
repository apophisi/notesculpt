import time
import openai
from openai import OpenAI
from notesculpt.models import Config
from notesculpt.errors import (
    NoteSculptError,
    RateLimitError,
    NetworkError,
    ServerError,
    AuthError,
    FatalError,
)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


class LLMClient:
    def __init__(self, config: Config):
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self._model = config.model

    def refine(self, system_prompt: str, user_content: str) -> str:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.3,
                )
                content = response.choices[0].message.content
                if not content:
                    raise FatalError("LLM 返回空结果")
                return content
            except NoteSculptError:
                raise
            except Exception as e:
                last_error = self._classify_error(e)
                if isinstance(last_error, FatalError):
                    raise last_error
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                raise last_error
        raise last_error  # pragma: no cover

    def _classify_error(self, error: Exception) -> NoteSculptError:
        if isinstance(error, openai.AuthenticationError):
            return AuthError(str(error))
        if isinstance(error, openai.RateLimitError):
            return RateLimitError(str(error))
        if isinstance(error, (openai.APIConnectionError, openai.APITimeoutError)):
            return NetworkError(str(error))
        if isinstance(error, openai.APIStatusError):
            if error.status_code and 500 <= error.status_code < 600:
                return ServerError(str(error))
            return FatalError(str(error))
        return NoteSculptError(str(error))