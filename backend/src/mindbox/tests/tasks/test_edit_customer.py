import pytest

from mindbox.tasks import edit_customer


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def mock_mindbox_client(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.edit_customer")


def test_edit_customer(user, mock_mindbox_client):
    edit_customer(str(user.id))

    mock_mindbox_client.assert_called_once_with(email=user.username, first_name=user.first_name, last_name=user.last_name, birth_date=user.birthdate)
