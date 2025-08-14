import pytest
from django.utils import timezone

from users.services.user_signer_up import UserSignerUp, UserSignerUpException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def sign_up():
    return lambda data: UserSignerUp(**data)()


@pytest.fixture
def data():
    return {
        "username": "mail@vampiram.net",
        "first_name": "Gerard",
        "last_name": "Swieten",
    }


@pytest.fixture
def existing_user(factory):
    return factory.user(username="mail@vampiram.net", last_name="oh", first_name="not-Gerard", email_confirmed_at=None)


def test_create_user(sign_up, data):
    user = sign_up(data)

    user.refresh_from_db()
    assert user.username == "mail@vampiram.net"
    assert user.first_name == "Gerard"
    assert user.last_name == "Swieten"
    assert user.email_confirmed_at is None


def test_create_user_only_with_username(sign_up, data):
    del data["first_name"]
    del data["last_name"]

    user = sign_up(data)

    user.refresh_from_db()
    assert user.username == "mail@vampiram.net"
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.email_confirmed_at is None


def test_update_existing_user_data(sign_up, data, existing_user):
    sign_up(data)

    existing_user.refresh_from_db()
    assert existing_user.username == "mail@vampiram.net"
    assert existing_user.first_name == "Gerard"
    assert existing_user.last_name == "Swieten"
    assert existing_user.email_confirmed_at is None


def test_allow_to_sign_up_if_existing_user_with_such_username_is_not_confirm_email_yet(sign_up, data, existing_user):
    user = sign_up(data)

    assert existing_user == user


def test_do_not_sign_up_if_existing_user_with_such_username_confirmed_email(sign_up, data, existing_user):
    existing_user.setattr_and_save("email_confirmed_at", timezone.now())

    with pytest.raises(UserSignerUpException, match="User already registered."):
        sign_up(data)
