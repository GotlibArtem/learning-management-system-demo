from collections.abc import Callable
from functools import wraps
from typing import Any

from django.conf import settings


def mindbox_enabled(func: Callable[..., None]) -> Callable[..., None]:
    """Decorator to run method only if MINDBOX_ENABLED is True."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        if not settings.MINDBOX_ENABLED:
            return None
        return func(*args, **kwargs)

    return wrapper
