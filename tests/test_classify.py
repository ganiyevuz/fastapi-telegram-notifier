from __future__ import annotations

from telegram_notifier.choices import Level, Severity
from telegram_notifier.classify import classify_exception


class TestClassifyException:
    def test_default_classification(self) -> None:
        level, severity = classify_exception(ValueError("oops"))
        assert level == Level.ERROR
        assert severity == Severity.MODERATE

    def test_critical_memory_error(self) -> None:
        level, severity = classify_exception(MemoryError())
        assert level == Level.CRITICAL
        assert severity == Severity.CRITICAL

    def test_critical_recursion_error(self) -> None:
        level, severity = classify_exception(
            RecursionError("max depth")
        )
        assert level == Level.CRITICAL
        assert severity == Severity.CRITICAL

    def test_critical_system_exit(self) -> None:
        level, severity = classify_exception(SystemExit(1))
        assert level == Level.CRITICAL
        assert severity == Severity.CRITICAL

    def test_high_severity_connection_error(self) -> None:
        level, severity = classify_exception(
            ConnectionError("refused")
        )
        assert level == Level.ERROR
        assert severity == Severity.HIGH

    def test_high_severity_timeout_error(self) -> None:
        level, severity = classify_exception(
            TimeoutError("timed out")
        )
        assert level == Level.ERROR
        assert severity == Severity.HIGH

    def test_high_severity_file_not_found(self) -> None:
        level, severity = classify_exception(
            FileNotFoundError("missing")
        )
        assert level == Level.ERROR
        assert severity == Severity.HIGH

    def test_high_severity_os_error(self) -> None:
        level, severity = classify_exception(
            OSError("disk full")
        )
        assert level == Level.ERROR
        assert severity == Severity.HIGH

    def test_warning_http_exception(self) -> None:
        from fastapi import HTTPException

        exc = HTTPException(status_code=404, detail="not found")
        level, severity = classify_exception(exc)
        assert level == Level.WARNING
        assert severity == Severity.LOW

    def test_warning_request_validation_error(self) -> None:
        from fastapi.exceptions import RequestValidationError

        exc = RequestValidationError(errors=[])
        level, severity = classify_exception(exc)
        assert level == Level.WARNING
        assert severity == Severity.LOW

    def test_mro_based_classification(self) -> None:
        """Subclasses of known types should be classified."""

        class CustomConnectionError(ConnectionError):
            pass

        level, severity = classify_exception(
            CustomConnectionError("custom")
        )
        assert level == Level.ERROR
        assert severity == Severity.HIGH

    def test_unknown_exception_defaults(self) -> None:
        class MyCustomError(Exception):
            pass

        level, severity = classify_exception(
            MyCustomError("custom")
        )
        assert level == Level.ERROR
        assert severity == Severity.MODERATE

    def test_permission_error_is_high(self) -> None:
        level, severity = classify_exception(
            PermissionError("denied")
        )
        assert level == Level.ERROR
        assert severity == Severity.HIGH
