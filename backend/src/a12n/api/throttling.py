from rest_framework.throttling import AnonRateThrottle

from app.api.throttling import ConfigurableThrottlingMixin


class AuthAnonRateThrottle(ConfigurableThrottlingMixin, AnonRateThrottle):
    """Throttle for login by password."""

    scope = "anon-auth"


class AuthByEmailCodeAnonRateThrottle(ConfigurableThrottlingMixin, AnonRateThrottle):
    """Throttle for login by email code."""

    scope = "anon-email-code-auth"
