import jwt
import pytest
from requests import RequestException

from users.services.oauth_user_fetcher import OAuthUserFetcher, OAuthUserFetcherException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def social_data():
    return {
        "provider": "google-oauth2",
        "code": "dummy-code",
        "redirect_uri": "https://example.com/callback",
    }


@pytest.fixture
def mailru_social_data():
    return {
        "provider": "mailru",
        "code": "dummy-mailru-code",
        "redirect_uri": "https://example.com/callback",
    }


@pytest.fixture
def apple_social_data():
    return {
        "provider": "apple-id",
        "code": "dummy-apple-code",
        "redirect_uri": "https://example.com/callback",
    }


@pytest.fixture
def yandex_social_data():
    return {
        "provider": "yaru",
        "code": "dummy-yandex-code",
        "redirect_uri": "https://example.com/callback",
    }


@pytest.fixture(autouse=True)
def mock_provider_data(settings):
    settings.SOCIAL_AUTH_PROVIDERS = {
        "google-oauth2": {
            "auth_scheme": "Bearer",
            "client_id": "google-client-id",
            "client_secret": "google-client-secret",
            "token_url": "https://google.com/oauth/token",
            "userinfo_url": "https://google.com/userinfo",
        },
        "mailru": {
            "auth_scheme": "Bearer",
            "client_id": "mailru-client-id",
            "client_secret": "mailru-client-secret",
            "token_url": "https://mail.ru/oauth/token",
            "userinfo_url": "https://mail.ru/userinfo",
        },
        "apple-id": {
            "auth_scheme": "Bearer",
            "client_id": "apple-client-id",
            "client_secret": "apple-private-key",
            "token_url": "https://appleid.apple.com/auth/token",
            "userinfo_url": None,
        },
        "yaru": {
            "auth_scheme": "OAuth",
            "client_id": "yandex-client-id",
            "client_secret": "yandex-client-secret",
            "token_url": "https://yandex.ru/oauth/token",
            "userinfo_url": "https://login.yandex.ru/info",
        },
    }


@pytest.fixture
def mock_token_response(mocker):
    return mocker.patch("users.services.oauth_user_fetcher.requests.post")


@pytest.fixture
def mock_userinfo_response(mocker):
    return mocker.patch("users.services.oauth_user_fetcher.requests.get")


@pytest.fixture(autouse=True)
def mock_jwt_encode(mocker):
    return mocker.patch("users.services.oauth_user_fetcher.jwt.encode", return_value="dummy-client-secret")


def test_fetch_user_data_success_google(social_data, mock_token_response, mock_userinfo_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"access_token": "google-token"}

    mock_userinfo_response.return_value.status_code = 200
    mock_userinfo_response.return_value.json.return_value = {
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
    }

    user_data = OAuthUserFetcher(**social_data)()

    assert user_data["email"] == "user@example.com"
    assert user_data["first_name"] == "John"
    assert user_data["last_name"] == "Doe"


def test_fetch_user_data_success_mailru(mailru_social_data, mock_token_response, mock_userinfo_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"access_token": "mailru-token"}

    mock_userinfo_response.return_value.status_code = 200
    mock_userinfo_response.return_value.json.return_value = {
        "email": "mailru@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
    }

    user_data = OAuthUserFetcher(**mailru_social_data)()

    assert user_data["email"] == "mailru@example.com"
    assert user_data["first_name"] == "Jane"
    assert user_data["last_name"] == "Doe"


def test_fetch_user_data_success_yandex(yandex_social_data, mock_token_response, mock_userinfo_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"access_token": "yandex-token"}

    mock_userinfo_response.return_value.status_code = 200
    mock_userinfo_response.return_value.json.return_value = {
        "email": "yandex@example.com",
        "first_name": "Yandex",
        "last_name": "User",
    }

    user_data = OAuthUserFetcher(**yandex_social_data)()

    assert user_data["email"] == "yandex@example.com"
    assert user_data["first_name"] == "Yandex"
    assert user_data["last_name"] == "User"


def test_fetch_user_data_success_apple(apple_social_data, mock_token_response, mocker):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"id_token": "encoded.jwt.token"}

    decoded_jwt = {"email": "apple@example.com", "first_name": "Apple", "last_name": "User"}
    mocker.patch("users.services.oauth_user_fetcher.jwt.decode", return_value=decoded_jwt)

    user_data = OAuthUserFetcher(**apple_social_data).act()

    assert user_data["email"] == "apple@example.com"
    assert user_data["first_name"] == "Apple"
    assert user_data["last_name"] == "User"


def test_raises_on_provider_not_supported():
    with pytest.raises(OAuthUserFetcherException, match="Unsupported social provider."):
        OAuthUserFetcher(provider="unknown", code="dummy", redirect_uri="https://example.com/callback")()


def test_raises_on_token_exchange_failure(social_data, mock_token_response):
    mock_token_response.return_value.status_code = 400
    mock_token_response.return_value.text = "invalid_request"

    with pytest.raises(OAuthUserFetcherException, match="Failed to exchange code. Status: 400, Response: invalid_request"):
        OAuthUserFetcher(**social_data)()


def test_raises_on_network_failure(social_data, mock_token_response):
    mock_token_response.side_effect = RequestException("Network error")

    with pytest.raises(OAuthUserFetcherException, match="Failed to request access token."):
        OAuthUserFetcher(**social_data)()


def test_raises_when_email_not_provided(social_data, mock_token_response, mock_userinfo_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"access_token": "google-token"}

    mock_userinfo_response.return_value.status_code = 200
    mock_userinfo_response.return_value.json.return_value = {"first_name": "John", "last_name": "Doe"}

    with pytest.raises(OAuthUserFetcherException, match="Email was not provided by the social provider."):
        OAuthUserFetcher(**social_data)()


def test_raises_when_id_token_missing(apple_social_data, mock_token_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {}

    with pytest.raises(OAuthUserFetcherException, match="id_token not provided by Apple."):
        OAuthUserFetcher(**apple_social_data)()


def test_raises_on_apple_jwt_decode_error(apple_social_data, mock_token_response, mocker):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"id_token": "invalid-token"}

    mocker.patch("users.services.oauth_user_fetcher.jwt.decode", side_effect=jwt.PyJWTError)

    with pytest.raises(OAuthUserFetcherException, match="Failed to decode id_token from Apple."):
        OAuthUserFetcher(**apple_social_data)()


def test_raises_on_userinfo_fetch_failure(social_data, mock_token_response, mock_userinfo_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"access_token": "google-token"}

    mock_userinfo_response.return_value.status_code = 400

    with pytest.raises(OAuthUserFetcherException, match="Failed to fetch user info from provider."):
        OAuthUserFetcher(**social_data)()


def test_raises_when_yandex_email_not_provided(yandex_social_data, mock_token_response, mock_userinfo_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"access_token": "yandex-token"}

    mock_userinfo_response.return_value.status_code = 200
    mock_userinfo_response.return_value.json.return_value = {"first_name": "Yandex", "last_name": "User"}

    with pytest.raises(OAuthUserFetcherException, match="Email was not provided by the social provider."):
        OAuthUserFetcher(**yandex_social_data)()


def test_raises_on_yandex_userinfo_fetch_failure(yandex_social_data, mock_token_response, mock_userinfo_response):
    mock_token_response.return_value.status_code = 200
    mock_token_response.return_value.json.return_value = {"access_token": "yandex-token"}

    mock_userinfo_response.return_value.status_code = 400

    with pytest.raises(OAuthUserFetcherException, match="Failed to fetch user info from provider."):
        OAuthUserFetcher(**yandex_social_data)()
