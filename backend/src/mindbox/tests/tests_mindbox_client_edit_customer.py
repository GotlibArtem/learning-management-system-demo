from datetime import date

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

    get_client().edit_customer(
        email="student@example.com",
        first_name="John",
        last_name="Doe",
        birth_date=date(1990, 1, 1),
    )

    assert mock_mindbox_request.call_count == int(enabled)


def test_mindbox_operation_parameters(get_client, mock_mindbox_request):
    get_client().edit_customer(
        email="student@example.com",
        first_name="John",
        last_name="Doe",
        birth_date=date(1990, 1, 1),
    )

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=LMSEditCustomer",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": "student@example.com",
                "firstName": "John",
                "lastName": "Doe",
                "birthDate": "1990-01-01",
            },
        },
        raise_for_status=False,
    )


def test_raise_on_mindbox_operation_error_status(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "Success"}, 500)

    with pytest.raises(MindboxClientException, match="Mindbox operation error! Status: 500"):
        get_client().edit_customer(
            email="student@example.com",
            first_name="John",
            last_name="Doe",
            birth_date=date(1990, 1, 1),
        )


def test_raise_on_mindbox_operation_error_message(get_client, mock_mindbox_request):
    mock_mindbox_request.return_value = ({"status": "TOTALLY NOT OK!!!"}, 200)

    with pytest.raises(MindboxClientException, match="TOTALLY NOT OK!!!"):
        get_client().edit_customer(
            email="student@example.com",
            first_name="John",
            last_name="Doe",
            birth_date=date(1990, 1, 1),
        )


def test_write_to_log_on_success(get_client, mock_mindbox_request):
    get_client().edit_customer(
        email="student@example.com",
        first_name="John",
        last_name="Doe",
        birth_date=date(1990, 1, 1),
    )

    log = MindboxOperationLog.objects.last()

    assert log.operation == "LMSEditCustomer"
    assert log.content == {
        "customer": {
            "email": "student@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "birthDate": "1990-01-01",
        },
    }


def test_send_customer_interests(get_client, mock_mindbox_request):
    get_client().edit_customer(
        email="student@example.com",
        interests=["cinema", "art", "music"],
    )

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=LMSEditCustomer",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": "student@example.com",
                "customFields": {
                    "interesLMS": ["cinema", "art", "music"],
                },
            },
        },
        raise_for_status=False,
    )


def test_edit_customer_without_optional_fields(get_client, mock_mindbox_request):
    get_client().edit_customer(email="student@example.com")

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=LMSEditCustomer",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": "student@example.com",
            },
        },
        raise_for_status=False,
    )


def test_edit_customer_with_full_data(get_client, mock_mindbox_request):
    get_client().edit_customer(
        email="student@example.com",
        first_name="John",
        last_name="Doe",
        birth_date=date(1990, 1, 1),
        interests=["all-interests"],
    )

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=LMSEditCustomer",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": "student@example.com",
                "firstName": "John",
                "lastName": "Doe",
                "birthDate": "1990-01-01",
                "customFields": {
                    "interesLMS": ["all-interests"],
                },
            },
        },
        raise_for_status=False,
    )
