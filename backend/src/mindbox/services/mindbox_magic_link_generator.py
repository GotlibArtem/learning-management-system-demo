from dataclasses import dataclass
from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.utils.functional import cached_property

from a12n.models import PasswordlessEmailAuthCode
from app.services import BaseService
from users.models import User
from users.services import UserEditor


@dataclass
class MindboxMagicLinkGenerator(BaseService):
    username: str

    def act(self) -> str:
        auth_code = PasswordlessEmailAuthCode.objects.create(user=self.user)
        magic_link_page = "/product-checkedout/"
        encoded_magic_link_params = urlencode({"email": self.username, "code": auth_code.code})
        return urljoin(settings.ABSOLUTE_URL, f"{magic_link_page}?{encoded_magic_link_params}")

    @cached_property
    def user(self) -> User:
        return UserEditor(username=self.username)()[0]
