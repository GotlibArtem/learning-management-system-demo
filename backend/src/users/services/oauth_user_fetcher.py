import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jwt
import requests
from django.conf import settings
from django.db.transaction import atomic
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from app.exceptions import AppServiceException
from app.services import BaseService


class OAuthUserFetcherException(AppServiceException):
    """Raised if fetching user data via OAuth failed."""


@dataclass
class OAuthUserFetcher(BaseService):
    provider: str
    code: str
    redirect_uri: str

    @atomic
    def act(self) -> dict[str, Any]:
        user_data = self.fetch_user_data()

        return {
            "email": self.get_email(user_data),
            "first_name": user_data.get("first_name", "") or user_data.get("given_name", ""),
            "last_name": user_data.get("last_name", "") or user_data.get("family_name", ""),
        }

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_provider,
        ]

    def validate_provider(self) -> None:
        if self.provider_data is None:
            raise OAuthUserFetcherException(_("Unsupported social provider."))

    @cached_property
    def provider_data(self) -> dict[str, Any]:
        return settings.SOCIAL_AUTH_PROVIDERS.get(self.provider)

    def fetch_user_data(self) -> dict[str, Any]:
        handler_map = {
            "apple-id": self.handle_apple,
            "mailru": self.handle_mailru,
        }
        handler = handler_map.get(self.provider, self.handle_default)
        return handler()

    @cached_property
    def token_response(self) -> dict[str, Any]:
        try:
            response = requests.post(
                url=self.provider_data["token_url"],
                data={
                    "code": self.code,
                    "client_id": self.provider_data["client_id"],
                    "client_secret": self.get_client_secret(),
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=20,
            )
        except requests.RequestException as e:
            raise OAuthUserFetcherException(_("Failed to request access token.")) from e

        if response.status_code != status.HTTP_200_OK:
            raise OAuthUserFetcherException(
                _(f"Failed to exchange code. Status: {response.status_code}, Response: {response.text}"),
            )

        return response.json()

    def get_client_secret(self) -> str:
        if self.provider != "apple-id":
            return self.provider_data["client_secret"]

        headers = {"kid": settings.SOCIAL_AUTH_APPLE_ID_KEY}
        payload = {
            "iss": settings.SOCIAL_AUTH_APPLE_ID_TEAM,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400 * 30,
            "aud": "https://appleid.apple.com",
            "sub": self.provider_data["client_id"],
        }

        return jwt.encode(payload, self.provider_data["client_secret"], algorithm="ES256", headers=headers)

    def handle_apple(self) -> dict[str, Any]:
        id_token = self.token_response.get("id_token")
        if not id_token:
            raise OAuthUserFetcherException(_("id_token not provided by Apple."))

        try:
            return jwt.decode(id_token, options={"verify_signature": False})
        except jwt.PyJWTError:
            raise OAuthUserFetcherException(_("Failed to decode id_token from Apple."))

    def handle_mailru(self) -> dict[str, Any]:
        response = requests.get(
            url=self.provider_data["userinfo_url"],
            params={"access_token": self.get_access_token()},
            timeout=20,
        )

        if response.status_code != status.HTTP_200_OK:
            raise OAuthUserFetcherException(_("Failed to fetch user info from Mail.ru."))

        return response.json()

    def handle_default(self) -> dict[str, Any]:
        response = requests.get(
            url=self.provider_data["userinfo_url"],
            headers={"Authorization": f"{self.provider_data['auth_scheme']} {self.get_access_token()}"},
            timeout=20,
        )

        if response.status_code != status.HTTP_200_OK:
            raise OAuthUserFetcherException(_("Failed to fetch user info from provider."))

        return response.json()

    def get_access_token(self) -> str:
        access_token = self.token_response.get("access_token")
        if not access_token:
            raise OAuthUserFetcherException(_("Access token not provided."))
        return access_token

    def get_email(self, user_data: dict[str, Any]) -> str:
        email = user_data.get("email") or user_data.get("default_email", "")
        if not email:
            raise OAuthUserFetcherException(_("Email was not provided by the social provider."))
        return email
