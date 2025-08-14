import pytest

from users.services.user_comment_token_getter import CommentAuthData


pytestmark = [
    pytest.mark.django_db,
]

base_url = "/api/demo/users/me/comment-auth/"


@pytest.fixture
def mock_comment_token_getter(mocker):
    return mocker.patch(
        "users.services.user_comment_token_getter.UserCommentTokenGetter.act",
        return_value=CommentAuthData(user_json_base64="test_user_json_base64", signature="test_signature", current_time_ms="test_current_time_ms"),
    )


def test_get_comment_token(as_user, mock_comment_token_getter):
    response = as_user.get(base_url)

    assert response["userJsonBase64"] == mock_comment_token_getter.return_value["user_json_base64"]
    assert response["signature"] == mock_comment_token_getter.return_value["signature"]
    assert response["currentTimeMs"] == mock_comment_token_getter.return_value["current_time_ms"]
