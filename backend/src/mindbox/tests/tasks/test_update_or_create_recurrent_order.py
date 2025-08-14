from datetime import timedelta

import pytest
from django.utils.timezone import now

from mindbox.tasks import update_or_create_recurrent_order
from product_access.models import ProductAccess


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def mock_mindbox_client(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.update_or_create_recurrent_order")


@pytest.fixture
def recurrent_subscription(user, product, recurrent):
    product.setattr_and_save("product_type", "subscription")
    recurrent.setattr_and_save("user", user)
    recurrent.setattr_and_save("product", product)
    recurrent.setattr_and_save("next_charge_date", now())

    return recurrent


def test_update_or_create_recurrent_order(user, recurrent_subscription, mock_mindbox_client):
    update_or_create_recurrent_order(str(user.id), str(recurrent_subscription.id))

    product_access = ProductAccess.objects.filter(user=user, product=recurrent_subscription.product).first()
    next_charge_date = (
        recurrent_subscription.next_charge_date.date()
        if recurrent_subscription.next_charge_date
        else (product_access.end_date.date() + timedelta(days=product_access.product.lifetime))
    )

    mock_mindbox_client.assert_called_once_with(
        email=user.username,
        subscription_last_date=product_access.end_date.date() if product_access else None,
        next_charge_date=next_charge_date,
        amount=recurrent_subscription.amount,
    )
