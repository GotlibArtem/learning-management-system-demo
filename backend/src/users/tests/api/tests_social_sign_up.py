import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import SlidingToken

from users.models import User
from users.services import OAuthUserFetcherException


pytestmark = [
    pytest.mark.django_db,
]

base_url = "/api/demo/users/social-sign-up/"


@pytest.fixture
def data():
    return {
        "provider": "google-oauth2",
        "code": "dummy-code",
        "redirect_uri": "https://example.com/callback",
    }


@pytest.fixture
def mock_backend_user(mocker):
    user = mocker.Mock()
    user.email = "social@email.com"
    user.first_name = "Alice"
    user.last_name = "Smith"
    return user


@pytest.fixture(autouse=True)
def mock_oauth_user_fetcher(mocker, mock_backend_user):
    return mocker.patch(
        "users.api.viewsets.OAuthUserFetcher",
        return_value=lambda: {
            "email": mock_backend_user.email,
            "first_name": mock_backend_user.first_name,
            "last_name": mock_backend_user.last_name,
        },
    )


def test_creates_user_with_token_and_correct_profile(as_anon, data):
    got = as_anon.post(base_url, data=data, expected_status=200)

    assert "token" in got
    assert len(got["token"]) > 40

    token = SlidingToken(got["token"])
    user_id = token["user_id"]

    user = User.objects.get(id=user_id)

    assert user.username == "social@email.com"
    assert user.first_name == "Alice"
    assert user.last_name == "Smith"


def test_reuses_user_if_email_not_confirmed(as_anon, data, factory):
    existing = factory.user(username="social@email.com", email_confirmed_at=None)

    got = as_anon.post(base_url, data=data, expected_status=200)

    token = SlidingToken(got["token"])

    assert str(existing.id) == token["user_id"]


def test_returns_400_if_email_already_confirmed(as_anon, data, factory):
    factory.user(username="social@email.com", email_confirmed_at=timezone.now())

    got = as_anon.post(base_url, data=data, expected_status=400)

    assert "serviceError" in got
    assert "User already registered" in got["serviceError"]


def test_returns_400_if_did_not_return_email(as_anon, data, mock_oauth_user_fetcher):
    mock_oauth_user_fetcher.side_effect = OAuthUserFetcherException("Social provider did not return email.")

    got = as_anon.post(base_url, data=data, expected_status=400)

    assert "serviceError" in got
    assert "Social provider did not return email" in got["serviceError"]


def test_returns_400_if_provider_is_missing(as_anon, data):
    del data["provider"]

    got = as_anon.post(base_url, data=data, expected_status=400)

    assert "provider" in got


def test_returns_400_if_code_is_missing(as_anon, data):
    del data["code"]

    got = as_anon.post(base_url, data=data, expected_status=400)

    assert "code" in got
