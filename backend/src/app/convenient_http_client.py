from dataclasses import dataclass
from json import JSONDecodeError
from urllib.parse import urljoin

import requests
from django.utils.functional import cached_property


@dataclass
class ConvenientHTTPClient:
    base_url: str

    def request(
        self,
        *,
        method: str,
        endpoint: str,
        data: dict | None = None,
        headers: dict[str, str] | None = None,
        raise_for_status: bool = True,
    ) -> tuple[dict, int]:
        response = getattr(requests, method)(
            self._join_url(path=endpoint),
            headers=self._get_headers(headers),
            json=data,
        )

        if raise_for_status:
            response.raise_for_status()

        try:
            serialized_response = response.json()
        except JSONDecodeError:
            serialized_response = {}

        return serialized_response, response.status_code

    @staticmethod
    def _get_headers(update_headers: dict[str, str] | None = None) -> dict:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if update_headers:
            headers.update(update_headers)

        return headers

    def _join_url(self, *, path: str) -> str:
        return urljoin(self.cleaned_base_url, f"{path}")

    @cached_property
    def cleaned_base_url(self) -> str:
        if self.base_url.endswith("/"):
            return self.base_url

        return f"{self.base_url}/"
