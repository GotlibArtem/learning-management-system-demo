import pytest

from a12n.models import PasswordlessEmailAuthCode
from mindbox.services import MindboxMagicLinkGenerator
from users.models import User


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.ABSOLUTE_URL = "https://the-frontend.lms.comx"


@pytest.fixture
def user(factory):
    return factory.user(username="jacksparrow@piratebay.com")


@pytest.fixture
def generator(user):
    return MindboxMagicLinkGenerator(username=user.username)


def test_user_token_created(generator, user):
    generator()

    auth_code = PasswordlessEmailAuthCode.objects.get()
    assert auth_code.user == user
    assert auth_code.code is not None


def test_auth_link(generator):
    auth_link = generator()

    code = PasswordlessEmailAuthCode.objects.get().code
    assert auth_link == f"https://the-frontend.lms.comx/product-checkedout/?email=jacksparrow%40piratebay.com&code={code}"


def test_nonexistent_user_created(generator, user):
    user.delete()

    generator()

    user = User.objects.get()
    assert user.username == "jacksparrow@piratebay.com"
    assert user.email == "jacksparrow@piratebay.com"
    assert user.first_name == ""
    assert user.last_name == ""
