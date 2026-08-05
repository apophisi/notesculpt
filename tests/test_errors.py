from notesculpt.errors import (
    NoteSculptError,
    RetryableError,
    FatalError,
    RateLimitError,
    NetworkError,
    ServerError,
    AuthError,
    ConfigError,
    FileError,
)


class TestExceptionHierarchy:
    def test_base_exit_code(self):
        err = NoteSculptError("test")
        assert err.exit_code == 1

    def test_retryable_is_notesculpt_error(self):
        err = RetryableError("retry")
        assert isinstance(err, NoteSculptError)

    def test_fatal_is_notesculpt_error(self):
        err = FatalError("fatal")
        assert isinstance(err, NoteSculptError)

    def test_rate_limit_is_retryable(self):
        err = RateLimitError("rate limited")
        assert isinstance(err, RetryableError)

    def test_network_is_retryable(self):
        err = NetworkError("network down")
        assert isinstance(err, RetryableError)

    def test_server_is_retryable(self):
        err = ServerError("server error")
        assert isinstance(err, RetryableError)

    def test_auth_is_fatal(self):
        err = AuthError("invalid key")
        assert isinstance(err, FatalError)
        assert err.exit_code == 2

    def test_config_is_fatal(self):
        err = ConfigError("missing config")
        assert isinstance(err, FatalError)
        assert err.exit_code == 3

    def test_file_is_fatal(self):
        err = FileError("not found")
        assert isinstance(err, FatalError)
        assert err.exit_code == 4

    def test_error_message(self):
        err = NoteSculptError("something went wrong")
        assert str(err) == "something went wrong"