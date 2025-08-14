import pytest

from users.services import AuthCodeEmailContextBuilder


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.ABSOLUTE_URL = "https://the-frontend.lms.comx"


@pytest.fixture
def builder():
    return AuthCodeEmailContextBuilder(email="jacksparrow@piratebay.com", code="7777")


def test_magic_link_is_generated(builder):
    context = builder()

    assert context["AuthenticationLink"] == "https://the-frontend.lms.comx/auth?email=jacksparrow%40piratebay.com&code=7777"


def test_pass_code_into_context(builder):
    context = builder()

    assert context["AuthenticationCode"] == "7777"
