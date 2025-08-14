from datetime import UTC, datetime, timedelta

import pytest

from a12n.models import PasswordlessEmailAuthCode


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.freeze_time("2049-01-05 10:00:00"),
]


@pytest.fixture
def create_auth_code():
    return lambda user: PasswordlessEmailAuthCode.objects.create(user=user)


def test_created_code_is_long_enough(create_auth_code, user, settings):
    settings.PASSWORDLESS_EMAIL_CODE_LENGTH = 6

    auth_code = create_auth_code(user)

    assert len(auth_code.code) == 6


def test_created_code_is_numeric(create_auth_code, user):
    auth_code = create_auth_code(user)

    for char in auth_code.code:
        assert char.isdigit()


def test_created_code_is_new_every_time(create_auth_code, user):
    code_one = create_auth_code(user).code
    code_two = create_auth_code(user).code
    code_three = create_auth_code(user).code

    assert len({code_one, code_two, code_three}) == 3


def test_created_code_default_fields(create_auth_code, user):
    auth_code = create_auth_code(user)

    auth_code.refresh_from_db()
    assert auth_code.user == user
    assert auth_code.used is None


def test_created_code_expiration_time_is_in_future(create_auth_code, user, settings):
    settings.PASSWORDLESS_EMAIL_CODE_EXPIRATION_TIME = timedelta(minutes=30)

    auth_code = create_auth_code(user)

    auth_code.refresh_from_db()
    assert auth_code.expires == datetime(2049, 1, 5, 10, 30, 0, tzinfo=UTC)
