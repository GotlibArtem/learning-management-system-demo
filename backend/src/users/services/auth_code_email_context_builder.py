from dataclasses import dataclass
from urllib.parse import urlencode, urljoin

from django.conf import settings

from app.services import BaseService


@dataclass
class AuthCodeEmailContextBuilder(BaseService):
    email: str
    code: str

    def act(self) -> dict[str, str]:
        magic_link_page = "/auth"
        encoded_magic_link_params = urlencode({"email": self.email, "code": self.code})

        frontend_magic_link = urljoin(settings.ABSOLUTE_URL, f"{magic_link_page}?{encoded_magic_link_params}")

        return {
            "AuthenticationCode": self.code,
            "AuthenticationLink": frontend_magic_link,
        }
