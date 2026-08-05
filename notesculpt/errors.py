class NoteSculptError(Exception):
    exit_code: int = 1

    def __init__(self, message: str):
        super().__init__(message)


class RetryableError(NoteSculptError):
    pass


class RateLimitError(RetryableError):
    pass


class NetworkError(RetryableError):
    pass


class ServerError(RetryableError):
    pass


class FatalError(NoteSculptError):
    pass


class AuthError(FatalError):
    exit_code = 2


class ConfigError(FatalError):
    exit_code = 3


class FileError(FatalError):
    exit_code = 4
