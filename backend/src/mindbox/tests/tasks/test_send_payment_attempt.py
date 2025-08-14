import pytest
from django.utils.timezone import now

from mindbox.tasks import send_payment_attempt
from payments.models import RecurrentChargeAttempt, RecurrentChargeStatus


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def mock_mindbox_client(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.send_payment_attempt")


@pytest.fixture
def recurrent_charge_attempt(factory, user, product, payment, payment_instrument, recurrent):
    product.setattr_and_save("product_type", "subscription")
    recurrent.setattr_and_save("user", user)
    recurrent.setattr_and_save("product", product)
    recurrent.setattr_and_save("next_charge_date", now())
    payment.setattr_and_save("user", user)
    payment.setattr_and_save("product", product)
    payment.setattr_and_save("payment_instrument", payment_instrument)

    return factory.recurrent_charge_attempt(recurrent=recurrent, payment=payment)


def test_send_payment_attempt(user, mock_mindbox_client, recurrent_charge_attempt):
    send_payment_attempt(str(user.id), str(recurrent_charge_attempt.id))

    attempts_count = RecurrentChargeAttempt.objects.filter(
        recurrent=recurrent_charge_attempt.recurrent,
        created__gte=recurrent_charge_attempt.recurrent.next_charge_date,
    ).count()

    attempt_success = recurrent_charge_attempt.status == RecurrentChargeStatus.SUCCESS

    mock_mindbox_client.assert_called_once_with(email=user.username, num_attempt=f"{attempts_count}attempt", attempt_success=attempt_success)
