from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time

from a12n.models import PasswordlessEmailAuthCode


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.freeze_time("2049-01-05 10:00:00"),
]


@pytest.fixture
def create_auth_code():
    def _create_auth_code(user, hacked_code=None):
        auth_code = PasswordlessEmailAuthCode.objects.create(user=user)
        if hacked_code:
            auth_code.code = hacked_code
            auth_code.save()

        return auth_code

    return _create_auth_code


def test_mark_as_used(create_auth_code, user):
    auth_code = create_auth_code(user)

    auth_code.mark_as_used()

    auth_code.refresh_from_db()
    assert auth_code.used == datetime(2049, 1, 5, 10, 00, 0, tzinfo=UTC)  # Froze Now()


def test_created_code_is_valid(create_auth_code, user):
    auth_code = create_auth_code(user, "123456")

    got_code = PasswordlessEmailAuthCode.objects.get_valid_code(user, "123456")

    assert auth_code == got_code


def test_not_matched_code_is_not_valid(create_auth_code, user):
    create_auth_code(user, "123456")

    got_code = PasswordlessEmailAuthCode.objects.get_valid_code(user, "111111")

    assert got_code is None


def test_used_code_is_not_valid(create_auth_code, user):
    auth_code = create_auth_code(user, "123456")
    auth_code.mark_as_used()

    got_code = PasswordlessEmailAuthCode.objects.get_valid_code(user, "123456")

    assert got_code is None


def test_same_code_for_another_user_is_not_valid(create_auth_code, user, factory):
    create_auth_code(factory.user(), "123456")

    got_code = PasswordlessEmailAuthCode.objects.get_valid_code(user, "123456")

    assert got_code is None


def test_expired_code_is_not_valid(create_auth_code, user, settings):
    settings.PASSWORDLESS_EMAIL_CODE_EXPIRATION_TIME = timedelta(minutes=30)
    create_auth_code(user, "123456")

    with freeze_time("2049-01-05 10:32:00"):
        got_code = PasswordlessEmailAuthCode.objects.get_valid_code(user, "123456")

    assert got_code is None
