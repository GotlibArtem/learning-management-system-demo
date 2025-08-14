import pytest
from rest_framework_simplejwt.tokens import SlidingToken


pytestmark = [
    pytest.mark.django_db,
]

base_url = "/api/demo/users/me/deactivate/"


@pytest.fixture
def user(factory):
    return factory.user(username="varya@gemail.comx", is_active=True)


@pytest.fixture
def token(user):
    return str(SlidingToken.for_user(user))


def test_deactivate_user(as_user, user):
    assert user.is_active is True

    as_user.post(base_url, expected_status=204)

    user.refresh_from_db()

    assert user.is_active is False


def test_deactivate_twice_fails(as_user, user):
    as_user.post(base_url, expected_status=204)

    user.refresh_from_db()

    assert user.is_active is False

    got = as_user.post(base_url, expected_status=401)

    assert "user inactive" in got["detail"].lower()


def test_deactivated_user_cannot_refresh_token(as_anon, user, token):
    user.is_active = False
    user.save()

    got = as_anon.post(
        "/api/demo/auth/token/refresh/",
        data={"token": token},
        expected_status=401,
    )

    assert "inactive user" in got["detail"].lower()
