from collections.abc import Callable
from typing import Any

import requests
from django.conf import settings
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest


class AuthenticatedProxySession(requests.Session):
    """Session with SOCKS5 proxy and optional OAuth authentication."""

    def __init__(
        self,
        proxy_url: str | None = None,
        credentials: Credentials | None = None,
        verify_ssl: bool = True,
        auto_refresh: bool = True,
        request_factory: Callable[[], GoogleAuthRequest] | None = None,
    ) -> None:
        super().__init__()

        if proxy_url:
            self.proxies = {"http": proxy_url, "https": proxy_url}

        self.verify = verify_ssl
        self.credentials = credentials
        self.auto_refresh = auto_refresh
        self.request_factory = request_factory

        self.is_mtls = False  # required for some Google clients

    def _refresh_token_if_needed(self) -> None:
        if self.credentials and self.auto_refresh and not self.credentials.valid and self.request_factory:
            self.credentials.refresh(self.request_factory())  # type: ignore[no-untyped-call]

    def _attach_auth_header(self, kwargs: dict[str, Any]) -> None:
        if self.credentials and self.credentials.token:
            headers = kwargs.setdefault("headers", {})
            headers["Authorization"] = f"Bearer {self.credentials.token}"

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:  # type: ignore[override]
        if self.credentials:
            self._refresh_token_if_needed()
            self._attach_auth_header(kwargs)
        if "timeout" not in kwargs:
            kwargs["timeout"] = 10
        return super().request(method, url, **kwargs)


def create_google_proxy_session(
    credentials: Credentials | None = None,
    proxy_url: str | None = None,
    verify_ssl: bool | None = None,
    auto_refresh: bool = True,
) -> AuthenticatedProxySession:
    import google.auth.transport.requests

    return AuthenticatedProxySession(
        proxy_url=proxy_url or getattr(settings, "PROXY_URL", None),
        credentials=credentials,
        verify_ssl=verify_ssl if verify_ssl is not None else getattr(settings, "PROXY_VERIFY_SSL", True),
        auto_refresh=auto_refresh,
        request_factory=lambda: google.auth.transport.requests.Request(),  # type: ignore[no-untyped-call]
    )


def create_generic_proxy_session(
    proxy_url: str | None = None,
    verify_ssl: bool | None = None,
) -> AuthenticatedProxySession:
    return AuthenticatedProxySession(
        proxy_url=proxy_url or getattr(settings, "PROXY_URL", None),
        credentials=None,
        verify_ssl=verify_ssl if verify_ssl is not None else getattr(settings, "PROXY_VERIFY_SSL", True),
        auto_refresh=False,
        request_factory=None,
    )
