"""معالجة الأخطاء والعمليات قابلة للإعادة"""
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar("T")


class RetryConfig:
    """إعدادات الإعادة"""

    def __init__(
        self,
        max_attempts: int = 3,
        wait_base: float = 1.0,
        wait_multiplier: float = 2.0,
        wait_max: int = 10,
    ):
        self.max_attempts = max_attempts
        self.wait_base = wait_base
        self.wait_multiplier = wait_multiplier
        self.wait_max = wait_max


def retry_on_exception(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
):
    """ديكوريتور لإعادة محاولة الدالة عند فشلها"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in Retrying(
                stop=stop_after_attempt(config.max_attempts),
                wait=wait_exponential(
                    multiplier=config.wait_multiplier,
                    min=config.wait_base,
                    max=config.wait_max,
                ),
                retry=retry_if_exception_type(exceptions),
                reraise=True,
            ):
                with attempt:
                    try:
                        logger.debug(
                            f"محاولة تنفيذ {func.__name__} (محاولة {attempt.retry_state.attempt_number})"
                        )
                        return func(*args, **kwargs)
                    except exceptions as e:
                        logger.warning(
                            f"فشل {func.__name__}: {e} (محاولة {attempt.retry_state.attempt_number}/{config.max_attempts})"
                        )
                        raise

        return wrapper

    return decorator


class ApplicationError(Exception):
    """خطأ عام للتطبيق"""

    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class EmailError(ApplicationError):
    """خطأ متعلق بالبريد الإلكتروني"""

    def __init__(self, message: str, code: str = "EMAIL_ERROR"):
        super().__init__(message, code, 500)


class DatabaseError(ApplicationError):
    """خطأ متعلق بقاعدة البيانات"""

    def __init__(self, message: str, code: str = "DATABASE_ERROR"):
        super().__init__(message, code, 500)


class ValidationError(ApplicationError):
    """خطأ التحقق من البيانات"""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code, 400)
