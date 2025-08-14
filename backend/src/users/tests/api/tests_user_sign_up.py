import pytest
from django.utils import timezone

from a12n.models import PasswordlessEmailAuthCode
from users.models import User


pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("mock_auth_code_task")]

base_url = "/api/demo/users/sign-up/"


@pytest.fixture
def data():
    return {
        "username": "varya@gemail.comx",
        "firstName": "Varvara",
        "lastName": "Perova",
    }


def test_sign_up_response(as_anon, data):
    got = as_anon.post(base_url, data=data)

    assert got["id"] is not None


@pytest.mark.parametrize("username", ["varya@gemail.comx", "VarYA@gemail.comx", "    vaRya@gemail.comx"])
def test_user_created(as_anon, data, username):
    data["username"] = username

    got = as_anon.post(base_url, data=data)

    user = User.objects.get(pk=got["id"])
    assert user.username == "varya@gemail.comx"
    assert user.email == "varya@gemail.comx"
    assert user.first_name == "Varvara"
    assert user.last_name == "Perova"


def test_user_token_created(as_anon, data):
    got = as_anon.post(base_url, data=data)

    auth_code = PasswordlessEmailAuthCode.objects.get(user=got["id"])
    assert auth_code.code is not None


def test_user_non_username_fields_are_optional_and_nullable(as_anon, data):
    del data["firstName"]
    data["lastName"] = None

    got = as_anon.post(base_url, data=data)

    user = User.objects.get(pk=got["id"])
    assert user.username == "varya@gemail.comx"
    assert user.email == "varya@gemail.comx"
    assert user.first_name == ""
    assert user.last_name == ""


def test_do_not_sign_up_if_user_already_confirm_email(as_anon, data, factory):
    factory.user(username="varya@gemail.comx", email_confirmed_at=timezone.now())

    got = as_anon.post(base_url, data=data, expected_status=400)

    assert "serviceError" in got
    assert "User already registered" in got["serviceError"]


def test_transform_creation_logic_exceptions_to_400(as_anon, data):
    data["username"] = "bad-email"

    got = as_anon.post(base_url, data=data, expected_status=400)

    assert "serviceError" in got
    assert "Invalid email" in got["serviceError"]


def test_mindbox_message_sent(as_anon, data, mock_auth_code_task):
    got = as_anon.post(base_url, data=data)

    auth_code = PasswordlessEmailAuthCode.objects.get(user=got["id"])

    mock_auth_code_task.assert_called_once_with(str(auth_code.id))


def test_do_not_send_mindbox_message_if_there_were_errors(as_anon, data, mock_auth_code_task):
    data["username"] = "bad-email"

    as_anon.post(base_url, data=data, expected_status=400)

    mock_auth_code_task.assert_not_called()
