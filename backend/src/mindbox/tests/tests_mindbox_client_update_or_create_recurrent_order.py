import pytest
from django.utils.timezone import now

from mindbox.models import MindboxOperationLog
from mindbox.services.client import MindboxClientException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def product_access(factory, user, product):
    return factory.product_access(user=user, product=product, end_date=now())


@pytest.fixture
def recurrent_subscription(user, product, recurrent):
    product.setattr_and_save("product_type", "subscription")
    recurrent.setattr_and_save("user", user)
    recurrent.setattr_and_save("product", product)
    recurrent.setattr_and_save("next_charge_date", now())

    return recurrent


@pytest.mark.parametrize(
    "enabled",
    [
        True,
        False,
    ],
)
def test_call_mindbox_operation_if_enabled(get_client, settings, enabled, mock_mindbox_request, user, recurrent_subscription, product_access):
    settings.MINDBOX_ENABLED = enabled

    get_client().update_or_create_recurrent_order(
        email=user.username,
        subscription_last_date=product_access.end_date.date(),
        next_charge_date=recurrent_subscription.next_charge_date.date(),
        amount=recurrent_subscription.amount,
    )

    assert mock_mindbox_request.call_count == int(enabled)


def test_mindbox_operation_parameters(get_client, mock_mindbox_request, user, recurrent_subscription, product_access):
    get_client().update_or_create_recurrent_order(
        email=user.username,
        subscription_last_date=product_access.end_date.date(),
        next_charge_date=recurrent_subscription.next_charge_date.date(),
        amount=recurrent_subscription.amount,
    )

    mock_mindbox_request.assert_called_once_with(
        method="post",
        endpoint="operations/sync?endpointId=TheEndpoint&operation=ReccurentOrder",
        headers={"Authorization": "SecretKey TheSecret"},
        data={
            "customer": {
                "email": user.username,
                "customFields": {
                    "subLastDay": product_access.end_date.date().isoformat(),
                    "nextPaymentDate": recurrent_subscription.next_charge_date.date().isoformat(),
                    "amountRecurrentPaid": recurrent_subscription.amount,
                },
            },
            "order": {
                "customFields": {
                    "rekurrent": True,
                },
            },
        },
        raise_for_status=False,
    )


def test_raise_on_mindbox_operation_error_status(get_client, mock_mindbox_request, user, recurrent_subscription, product_access):
    mock_mindbox_request.return_value = ({"status": "Success"}, 500)

    with pytest.raises(MindboxClientException, match="Mindbox operation error! Status: 500"):
        get_client().update_or_create_recurrent_order(
            email=user.username,
            subscription_last_date=product_access.end_date.date(),
            next_charge_date=recurrent_subscription.next_charge_date.date(),
            amount=recurrent_subscription.amount,
        )


def test_raise_on_mindbox_operation_error_message(get_client, mock_mindbox_request, user, recurrent_subscription, product_access):
    mock_mindbox_request.return_value = ({"status": "TOTALLY NOT OK!!!"}, 200)

    with pytest.raises(MindboxClientException, match="TOTALLY NOT OK!!!"):
        get_client().update_or_create_recurrent_order(
            email=user.username,
            subscription_last_date=product_access.end_date.date(),
            next_charge_date=recurrent_subscription.next_charge_date.date(),
            amount=recurrent_subscription.amount,
        )


def test_write_to_log_on_success(get_client, mock_mindbox_request, user, recurrent_subscription, product_access):
    get_client().update_or_create_recurrent_order(
        email=user.username,
        subscription_last_date=product_access.end_date.date(),
        next_charge_date=recurrent_subscription.next_charge_date.date(),
        amount=recurrent_subscription.amount,
    )

    log = MindboxOperationLog.objects.last()

    assert log.operation == "ReccurentOrder"
    assert log.content == {
        "customer": {
            "email": user.username,
            "customFields": {
                "subLastDay": product_access.end_date.date().isoformat(),
                "nextPaymentDate": recurrent_subscription.next_charge_date.date().isoformat(),
                "amountRecurrentPaid": recurrent_subscription.amount,
            },
        },
        "order": {
            "customFields": {
                "rekurrent": True,
            },
        },
    }
