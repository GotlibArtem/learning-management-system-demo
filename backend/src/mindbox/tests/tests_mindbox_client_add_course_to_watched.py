import pytest

from mindbox.models import MindboxOperationLog
from mindbox.services.client import MindboxClientException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.mark.parametrize(
    "enabled",
    [
        True,
        False,
    ],
)
def test_call_mindbox_operation_if_enabled(get_client, settings, enabled, mock_mindbox_request):
    settings.MINDBOX_ENABLED = enabled

    get_client().add_course_to_watched("student@example.com", "course-456")

    assert mock_mindbox_request.call_count == int(enabled)


def test_mindbox_operation_parameters(get_client, mock_mindbox_request):
    get_client().add_course_to_watched("student@example.com", "course-456")

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=AddProductToKursyKlientaItemList",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": "student@example.com",
            },
            "addProductToList": {
                "product": {
                    "ids": {
                        "website": "course-456",
                    },
                },
            },
        },
        raise_for_status=False,
    )


def test_raise_on_mindbox_operation_error_status(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "Success"}, 500)

    with pytest.raises(MindboxClientException, match="Mindbox operation error! Status: 500"):
        get_client().add_course_to_watched("student@example.com", "course-456")


def test_raise_on_mindbox_operation_error_message(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "TOTALLY NOT OK!!!"}, 200)

    with pytest.raises(MindboxClientException, match="TOTALLY NOT OK!!!"):
        get_client().add_course_to_watched("student@example.com", "course-456")


def test_write_to_log_on_success(get_client, mock_mindbox_request):
    get_client().add_course_to_watched("student@example.com", "course-456")

    log = MindboxOperationLog.objects.last()

    assert log.operation == "AddProductToKursyKlientaItemList"
    assert log.destination == ""
    assert log.content == {
        "customer": {
            "email": "student@example.com",
        },
        "addProductToList": {
            "product": {
                "ids": {
                    "website": "course-456",
                },
            },
        },
    }
