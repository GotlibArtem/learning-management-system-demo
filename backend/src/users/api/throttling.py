from rest_framework.throttling import AnonRateThrottle

from app.api.throttling import ConfigurableThrottlingMixin


class SignUpAnonRateThrottle(ConfigurableThrottlingMixin, AnonRateThrottle):
    """Throttle for registration and sending code view."""

    scope = "anon-sign-up"


class SignInAnonRateThrottle(ConfigurableThrottlingMixin, AnonRateThrottle):
    """Throttle for sending email code view."""

    scope = "anon-sign-in"
