import pytest

from mindbox.tasks import send_customer_interests


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def mock_mindbox_client(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.edit_customer")


def test_send_customer_interests_with_all_selected(user, mock_mindbox_client):
    user.all_interests = True
    user.save()

    send_customer_interests(str(user.id))

    mock_mindbox_client.assert_called_once_with(email=user.username, interests=["all-interests"])


def test_send_customer_interests_with_specific_interest(user, category, mock_mindbox_client):
    user.interests.set([category])
    user.all_interests = False
    user.save()

    send_customer_interests(str(user.id))

    mock_mindbox_client.assert_called_once_with(email=user.username, interests=["cinema"])


def test_send_customer_interests_with_no_interests_sends_empty_list(user, mock_mindbox_client):
    user.all_interests = False
    user.interests.clear()
    user.save()

    send_customer_interests(str(user.id))

    mock_mindbox_client.assert_called_once_with(
        email=user.username,
        interests=[],
    )
