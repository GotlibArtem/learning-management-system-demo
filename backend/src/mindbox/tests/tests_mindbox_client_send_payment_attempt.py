import pytest
from django.utils.timezone import now

from mindbox.models import MindboxOperationLog
from mindbox.services.client import MindboxClientException
from payments.models import RecurrentChargeAttempt, RecurrentChargeStatus


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def result_charge_attempt(factory, user, product, payment, payment_instrument, recurrent):
    product.setattr_and_save("product_type", "subscription")
    recurrent.setattr_and_save("user", user)
    recurrent.setattr_and_save("product", product)
    recurrent.setattr_and_save("next_charge_date", now())
    payment.setattr_and_save("user", user)
    payment.setattr_and_save("product", product)
    payment.setattr_and_save("payment_instrument", payment_instrument)
    recurrent_charge_attempt = factory.recurrent_charge_attempt(recurrent=recurrent, payment=payment)

    attempts_count = RecurrentChargeAttempt.objects.filter(
        recurrent=recurrent_charge_attempt.recurrent,
        created__gte=recurrent_charge_attempt.recurrent.next_charge_date,
    ).count()

    attempt_success = recurrent_charge_attempt.status == RecurrentChargeStatus.SUCCESS

    return f"{attempts_count}attempt", attempt_success


@pytest.mark.parametrize(
    "enabled",
    [
        True,
        False,
    ],
)
def test_call_mindbox_operation_if_enabled(get_client, settings, enabled, mock_mindbox_request, user, result_charge_attempt):
    settings.MINDBOX_ENABLED = enabled

    get_client().send_payment_attempt(
        email=user.username,
        num_attempt=result_charge_attempt[0],
        attempt_success=result_charge_attempt[1],
    )

    assert mock_mindbox_request.call_count == int(enabled)


def test_mindbox_operation_parameters(get_client, mock_mindbox_request, user, result_charge_attempt):
    get_client().send_payment_attempt(
        email=user.username,
        num_attempt=result_charge_attempt[0],
        attempt_success=result_charge_attempt[1],
    )

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=PaymentAttempt",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": user.username,
            },
            "customerAction": {
                "customFields": {
                    "nomerpopytki": result_charge_attempt[0],
                    "paymentSuccess": result_charge_attempt[1],
                },
            },
        },
        raise_for_status=False,
    )


def test_raise_on_mindbox_operation_error_status(get_client, mock_mindbox_request, user, result_charge_attempt):
    mock_mindbox_request.return_value = ({"status": "Success"}, 500)

    with pytest.raises(MindboxClientException, match="Mindbox operation error! Status: 500"):
        get_client().send_payment_attempt(
            email=user.username,
            num_attempt=result_charge_attempt[0],
            attempt_success=result_charge_attempt[1],
        )


def test_raise_on_mindbox_operation_error_message(get_client, mock_mindbox_request, user, result_charge_attempt):
    mock_mindbox_request.return_value = ({"status": "TOTALLY NOT OK!!!"}, 200)

    with pytest.raises(MindboxClientException, match="TOTALLY NOT OK!!!"):
        get_client().send_payment_attempt(
            email=user.username,
            num_attempt=result_charge_attempt[0],
            attempt_success=result_charge_attempt[1],
        )


def test_write_to_log_on_success(get_client, mock_mindbox_request, user, result_charge_attempt):
    get_client().send_payment_attempt(
        email=user.username,
        num_attempt=result_charge_attempt[0],
        attempt_success=result_charge_attempt[1],
    )

    log = MindboxOperationLog.objects.last()

    assert log.operation == "PaymentAttempt"
    assert log.content == {
        "customer": {
            "email": user.username,
        },
        "customerAction": {
            "customFields": {
                "nomerpopytki": result_charge_attempt[0],
                "paymentSuccess": result_charge_attempt[1],
            },
        },
    }
