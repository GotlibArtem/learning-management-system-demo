import pytest
from freezegun import freeze_time

from a12n.models import PasswordlessEmailAuthCode


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.freeze_time("2049-01-05 10:22"),
]


@pytest.fixture(autouse=True)
def mock_notify_task(mocker):
    return mocker.patch("mindbox.tasks.notify_user_logged_in.delay")


@pytest.fixture(autouse=True)
def create_auth_code(user):
    # Please, refactor me into reusable factory
    auth_code = PasswordlessEmailAuthCode.objects.create(user=user)
    auth_code.code = "123987"
    auth_code.save()

    return auth_code


@pytest.fixture
def get_tokens(as_anon):
    def _get_token(username, code, expected_status=200):
        return as_anon.post(
            "/api/demo/auth/token/obtain-by-email-code/",
            {
                "username": username,
                "code": code,
            },
            expected_status=expected_status,
        )

    return _get_token


def test_get_token(get_tokens):
    result = get_tokens("borisjohnson@mi6.uk", "123987")

    assert len(result["token"]) > 40


@pytest.mark.parametrize("username", ["Borisjohnson@mi6.uk", "   borisjohnson@mi6.uk   ", "borISjohnSON@mi6.uk"])
def test_get_token_with_different_email_formats(get_tokens, username):
    result = get_tokens(username, "123987")

    assert len(result["token"]) > 40


def test_disable_email_auth_code_after_usage(get_tokens):
    get_tokens("borisjohnson@mi6.uk", "123987")

    result = get_tokens("borisjohnson@mi6.uk", "123987", expected_status=400)  # Second usage

    assert "Invalid code" in result["serviceError"]


def test_user_confirms_email(get_tokens, user):
    get_tokens("borisjohnson@mi6.uk", "123987")

    user.refresh_from_db()
    assert user.email_confirmed_at is not None


def test_error_if_incorrect_code(get_tokens):
    result = get_tokens("borisjohnson@mi6.uk", "222111", expected_status=400)

    assert "Invalid code" in result["serviceError"]


def test_error_if_user_does_not_exist(get_tokens):
    result = get_tokens("cammalaharris@cia.gov", "123987", expected_status=400)

    assert "Account does not exist, try another one or create a new one." in result["serviceError"]


def test_error_if_user_is_not_active(get_tokens, user):
    user.setattr_and_save("is_active", False)

    result = get_tokens("borisjohnson@mi6.uk", "123987", expected_status=400)

    assert "Inactive user" in result["serviceError"]


def test_access_token_gives_access_to_correct_user(as_anon, user, get_tokens):
    access_token = get_tokens("borisjohnson@mi6.uk", "123987")["token"]

    as_anon.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    result = as_anon.get("/api/demo/users/me/")

    assert result["id"] == str(user.id)


def test_token_is_not_allowed_to_access_if_expired(as_anon, get_tokens):
    with freeze_time("2049-01-06 11:33"):
        result = get_tokens("borisjohnson@mi6.uk", "123987", expected_status=400)

    assert "Invalid code" in result["serviceError"]
