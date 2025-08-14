import pytest

from mindbox.tasks import notify_user_logged_in


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def mock_mindbox_client(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.user_logged_in")


def test_notify_user_logged_in(user, mock_mindbox_client):
    notify_user_logged_in(str(user.id), "device-123")

    mock_mindbox_client.assert_called_once_with(email=user.username, device_uuid="device-123")
