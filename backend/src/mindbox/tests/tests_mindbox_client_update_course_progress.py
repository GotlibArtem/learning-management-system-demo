import pytest

from mindbox.models import MindboxOperationLog
from mindbox.services.client import MindboxClientException
from mindbox.types import CourseProgressStatus


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

    get_client().update_course_progress("progress-123", CourseProgressStatus.FINISHED)

    assert mock_mindbox_request.call_count == int(enabled)


def test_mindbox_operation_parameters(get_client, mock_mindbox_request):
    get_client().update_course_progress("progress-123", CourseProgressStatus.FINISHED)

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=CourseProgressUpdate",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "orderLinesStatus": "CourseFinished",
            "order": {
                "ids": {
                    "externalID": "progress-123",
                },
            },
        },
        raise_for_status=False,
    )


def test_raise_on_mindbox_operation_error_status(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "Success"}, 500)

    with pytest.raises(MindboxClientException, match="Mindbox operation error! Status: 500"):
        get_client().update_course_progress("progress-123", CourseProgressStatus.FINISHED)


def test_raise_on_mindbox_operation_error_message(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "TOTALLY NOT OK!!!"}, 200)

    with pytest.raises(MindboxClientException, match="TOTALLY NOT OK!!!"):
        get_client().update_course_progress("progress-123", CourseProgressStatus.FINISHED)


def test_write_to_log_on_success(get_client, mock_mindbox_request):
    get_client().update_course_progress("progress-123", CourseProgressStatus.FINISHED)

    log = MindboxOperationLog.objects.last()

    assert log.operation == "CourseProgressUpdate"
    assert log.content == {
        "orderLinesStatus": "CourseFinished",
        "order": {
            "ids": {
                "externalID": "progress-123",
            },
        },
    }


@pytest.mark.parametrize("status", list(CourseProgressStatus))
def test_all_progress_statuses(get_client, mock_mindbox_request, status):
    get_client().update_course_progress("progress-123", status)

    mock_mindbox_request.assert_called_once()
    assert mock_mindbox_request.call_args[1]["data"]["orderLinesStatus"] == status
