import pytest
from freezegun import freeze_time
from rest_framework_simplejwt.tokens import SlidingToken


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.freeze_time("2049-01-05 10:22"),
]


@pytest.fixture
def refresh_token(as_anon):
    def _refresh_token(token, expected_status=200):
        return as_anon.post(
            "/api/demo/auth/token/refresh/",
            {
                "token": token,
            },
            expected_status=expected_status,
        )

    return _refresh_token


def test_refresh_token_endpoint(initial_token, refresh_token):
    refreshed_token = refresh_token(initial_token)

    assert len(refreshed_token["token"]) > 40


def test_refreshed_token_is_new(initial_token, refresh_token):
    refreshed_token = refresh_token(initial_token)

    assert initial_token != refreshed_token["token"]


def test_refreshed_token_works_as_access(initial_token, refresh_token, user, as_anon):
    refreshed_token = refresh_token(initial_token)["token"]

    as_anon.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed_token}")
    result = as_anon.get("/api/demo/users/me/")

    assert result["id"] == str(user.id)


def test_refreshed_token_works_as_refresh(initial_token, refresh_token, user, as_anon):
    refreshed_token = refresh_token(initial_token)["token"]
    last_refreshed_token = refresh_token(refreshed_token)["token"]

    as_anon.credentials(HTTP_AUTHORIZATION=f"Bearer {last_refreshed_token}")
    result = as_anon.get("/api/demo/users/me/")

    assert result["id"] == str(user.id)


def test_refresh_token_fails_if_user_is_not_active(refresh_token, initial_token, user):
    user.setattr_and_save("is_active", False)

    result = refresh_token(initial_token, expected_status=401)

    assert "Inactive user" in result["detail"]


def test_refresh_token_fails_with_incorrect_previous_token(refresh_token):
    result = refresh_token("some-invalid-previous-token", expected_status=401)

    assert "Token is invalid" in result["detail"]


def test_token_is_not_allowed_to_refresh_if_expired(initial_token, refresh_token):
    with freeze_time("2050-01-26 10:45"):
        result = refresh_token(initial_token, expected_status=401)

    assert "expired" in result["detail"]


def test_token_is_not_allowed_to_refresh_if_blacklisted(initial_token, refresh_token):
    SlidingToken(initial_token).blacklist()

    result = refresh_token(initial_token, expected_status=401)

    assert "blacklisted" in result["detail"]
