import pytest

from users.services import UserCommentTokenGetter


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def cackle_getter(user):
    return UserCommentTokenGetter(user=user)


def test_service(cackle_getter, settings):
    settings.CACKLE_API_KEY = "test_api_key"

    auth_key = cackle_getter()

    signature = auth_key["signature"]
    user_json_base64 = auth_key["user_json_base64"]
    current_time_ms = auth_key["current_time_ms"]

    assert isinstance(signature, str)
    assert isinstance(user_json_base64, str)
    assert isinstance(current_time_ms, str)
