import pytest

from mindbox.models import MindboxOperationLog
from mindbox.services.client import MindboxClientException


pytestmark = [
    pytest.mark.django_db,
]


def test_create_http_client_with_proper_params(get_client):
    client = get_client()

    assert client.mindbox_http.base_url == "https://mindbox.comx/demo/"


@pytest.mark.parametrize(
    "enabled",
    [
        True,
        False,
    ],
)
def test_call_mindbox_operation_if_enabled(get_client, settings, enabled, mock_mindbox_request):
    settings.MINDBOX_ENABLED = enabled

    get_client().run_email_operation("some-operation", "nekto@bay.conx", {"a": "b"})

    assert mock_mindbox_request.call_count == int(enabled)


def test_mindbox_operation_parameters(get_client, mock_mindbox_request):
    get_client().run_email_operation("some-operation", "nekto@bay.conx", {"a": "b"})

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=some-operation",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": "nekto@bay.conx",
            },
            "emailMailing": {
                "customParameters": {"a": "b"},
            },
        },
        raise_for_status=False,
    )


def test_raise_on_mindbox_operation_error_status(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "Success"}, 500)

    with pytest.raises(MindboxClientException, match="Mindbox operation error! Status: 500"):
        get_client().run_email_operation("some-operation", "nekto@bay.conx", {"a": "b"})


def test_raise_on_mindbox_operation_error_message(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "TOTALLY NOT OK!!!"}, 200)

    with pytest.raises(MindboxClientException, match="TOTALLY NOT OK!!!"):
        get_client().run_email_operation("some-operation", "nekto@bay.conx", {"a": "b"})


def test_write_to_log_on_success(get_client, mock_mindbox_request):
    get_client().run_email_operation("some-operation", "nekto@bay.conx", {"a": "b"})

    log = MindboxOperationLog.objects.last()

    assert log.operation == "some-operation"
    assert log.destination == "nekto@bay.conx"
    assert log.content == {
        "customer": {
            "email": "nekto@bay.conx",
        },
        "emailMailing": {
            "customParameters": {"a": "b"},
        },
    }
