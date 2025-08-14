from typing import Any

from django.http import Http404

from users.models import User


def associate_by_email(strategy: Any, details: dict[str, Any], backend: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    """
    Associate social account with existing user by email.
    This should be placed after 'social_core.pipeline.social_auth.social_user'
    and before 'social_core.pipeline.user.create_user' in the pipeline.
    """
    if kwargs.get("user"):
        return {}  # user is already associated, skip

    user = User.objects.filter(username__iexact=details.get("email")).first()
    if user:
        return {"user": user}

    raise Http404("User with such email not found")
