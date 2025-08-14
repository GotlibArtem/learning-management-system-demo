from django.contrib.auth.models import AnonymousUser

from app.testing import register
from app.testing.types import FactoryProtocol
from users.models import User


@register
def user(self: FactoryProtocol, **kwargs: dict) -> User:
    kwargs.setdefault("username", self.mixer.MIX.email)
    kwargs.setdefault("phone", self.mixer.faker.numerify("+7##########"))
    kwargs.setdefault("avatar_slug", self.mixer.RANDOM)
    kwargs.setdefault("first_name", self.mixer.RANDOM)
    kwargs.setdefault("last_name", self.mixer.RANDOM)
    return self.mixer.blend("users.User", **kwargs)


@register
def anon(self: FactoryProtocol, **kwargs: dict) -> AnonymousUser:
    return AnonymousUser()
