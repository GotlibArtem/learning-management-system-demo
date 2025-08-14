import pytest

from a12n.models import PasswordlessEmailAuthCode


pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("mock_auth_code_task")]

base_url = "/api/demo/users/sign-in/"


@pytest.fixture(autouse=True)
def user(factory):
    return factory.user(username="varya@gemail.comx")


@pytest.fixture
def data():
    return {
        "username": "varya@gemail.comx",
    }


@pytest.mark.parametrize("username", ["varya@gemail.comx", "VarYA@gemail.comx", "    vaRya@gemail.comx"])
def test_sign_in_response(as_anon, username):
    got = as_anon.post(base_url, data={"username": username}, expected_status=200)

    assert got["username"] == "varya@gemail.comx"


def test_user_token_created(as_anon, data, user):
    as_anon.post(base_url, data=data, expected_status=200)

    auth_code = PasswordlessEmailAuthCode.objects.get(user=user)
    assert auth_code.code is not None


def test_do_not_sign_in_if_user_does_not_exist(as_anon, data):
    data["username"] = "non@existant.comx"

    got = as_anon.post(base_url, data=data, expected_status=400)

    assert "serviceError" in got
    assert got["serviceError"] == "Account does not exist, try another one or create a new one."


def test_mindbox_message_sent(as_anon, data, mock_auth_code_task, user):
    as_anon.post(base_url, data=data, expected_status=200)

    auth_code = PasswordlessEmailAuthCode.objects.get(user=user)

    mock_auth_code_task.assert_called_once_with(str(auth_code.id))


def test_do_not_send_mindbox_message_if_there_were_errors(as_anon, data, mock_auth_code_task):
    data["username"] = "non@existant.comx"

    as_anon.post(base_url, data=data, expected_status=400)

    mock_auth_code_task.assert_not_called()


def test_sign_in_error_message_for_ios(as_anon, data):
    data["username"] = "non@existant.comx"
    got = as_anon.post(base_url, data=data, expected_status=400, headers={"Platform": "ios"})

    assert got["serviceError"] == "Account does not exist, try another one."
