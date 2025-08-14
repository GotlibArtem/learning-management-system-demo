import pytest
from axes.models import AccessAttempt
from freezegun import freeze_time


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.freeze_time("2049-01-05 10:22"),
]


@pytest.fixture
def get_tokens(as_anon):
    def _get_token(username, password, expected_status=200):
        return as_anon.post(
            "/api/demo/auth/token/obtain-by-password/",
            {
                "username": username,
                "password": password,
            },
            expected_status=expected_status,
        )

    return _get_token


def test_get_token(get_tokens):
    result = get_tokens("borisjohnson@mi6.uk", "sn00pd0g")

    assert len(result["token"]) > 40


def test_error_if_incorrect_password(as_anon, get_tokens):
    result = get_tokens("borisjohnson@mi6.uk", "50cent", expected_status=401)

    assert "No active account found with the given credentials" in result["detail"]


def test_error_if_user_is_not_active(get_tokens, user):
    user.setattr_and_save("is_active", False)

    result = get_tokens("borisjohnson@mi6.uk", "sn00pd0g", expected_status=401)

    assert "No active account found with the given credentials" in result["detail"]


def test_getting_token_with_incorrect_password_creates_access_attempt_log_entry(get_tokens):
    get_tokens("borisjohnson@mi6.uk", "50cent", expected_status=401)

    assert AccessAttempt.objects.count() == 1


def test_access_token_gives_access_to_correct_user(as_anon, user, get_tokens):
    access_token = get_tokens("borisjohnson@mi6.uk", "sn00pd0g")["token"]

    as_anon.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    result = as_anon.get("/api/demo/users/me/")

    assert result["id"] == str(user.id)


def test_token_is_not_allowed_to_access_if_expired(as_anon, get_tokens):
    access_token = get_tokens("borisjohnson@mi6.uk", "sn00pd0g")["token"]

    with freeze_time("2050-01-10 13:30"):
        as_anon.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        result = as_anon.get("/api/demo/users/me/", expected_status=401)

    assert "not valid" in result["detail"]
