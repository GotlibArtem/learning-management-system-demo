from datetime import UTC, datetime

import pytest
from freezegun import freeze_time

from users.services import UserEmailConfirmator


pytestmark = [pytest.mark.django_db, pytest.mark.freeze_time("2049-01-05 10:22")]


@pytest.fixture
def user(factory):
    user = factory.user(email_confirmed_at=None)

    assert user.email_confirmed_at is None

    return user


@pytest.fixture
def confirm_email():
    return lambda data: UserEmailConfirmator(**data)()


@pytest.fixture
def data(user):
    return {
        "user": user,
    }


def test_set_confirmation_date(confirm_email, data, user):
    confirm_email(data)

    user.refresh_from_db()
    assert user.email_confirmed_at == datetime(2049, 1, 5, 10, 22, 0, tzinfo=UTC)  # Froze Now()


def test_do_not_rewrite_confirmation_date_if_already_confirmed(confirm_email, data, user):
    confirm_email(data)

    with freeze_time("2049-01-26 10:45"):
        confirm_email(data)

    user.refresh_from_db()
    assert user.email_confirmed_at == datetime(2049, 1, 5, 10, 22, 0, tzinfo=UTC)  # Not changed
