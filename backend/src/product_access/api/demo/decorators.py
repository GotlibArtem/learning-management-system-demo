import traceback
from collections.abc import Callable
from typing import Any

import sentry_sdk
from django.db import InternalError, OperationalError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.exceptions import AppDatabaseException
from app.models import ShopDeadLetter


ViewMethod = Callable[..., Response]
Decorator = Callable[[ViewMethod], ViewMethod]


def dead_letter_creation(event_type: str) -> Decorator:
    def decorator(func: ViewMethod) -> ViewMethod:
        def drf_handler_method(self: APIView, request: Request, *args: Any, **kwargs: Any) -> Response:
            try:
                return func(self, request, *args, **kwargs)
            except (InternalError, OperationalError) as e:
                sentry_sdk.capture_exception(AppDatabaseException(e))
                raise AppDatabaseException(e)
            except Exception:
                ShopDeadLetter.objects.create(
                    event_type=event_type,
                    raw_data=request.data,
                    details=traceback.format_exc(),
                )
                raise

        return drf_handler_method

    return decorator
