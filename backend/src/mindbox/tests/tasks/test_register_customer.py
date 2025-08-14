import pytest

from mindbox.tasks import register_customer


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def mock_mindbox_client(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.register_customer")


def test_register_customer(user, mock_mindbox_client):
    register_customer(str(user.id))

    mock_mindbox_client.assert_called_once_with(email=user.username)
