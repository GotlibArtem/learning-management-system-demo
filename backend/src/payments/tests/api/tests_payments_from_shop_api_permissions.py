import pytest
from django.contrib.auth.models import Permission


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/payments/from-shop/"


def test_forbid_without_necessary_permission(as_shop_user, payment_data):
    payment_permission = Permission.objects.get(codename="allow_payment_integration")
    recurrent_permission = Permission.objects.get(codename="allow_recurrent_integration")

    as_shop_user.user.user_permissions.remove(payment_permission)
    as_shop_user.user.user_permissions.remove(recurrent_permission)

    as_shop_user.post(base_url, data=payment_data, expected_status=403)


def test_forbid_for_anon(as_anon, payment_data):
    as_anon.post(base_url, data=payment_data, expected_status=401)


def test_forbid_for_lms_user(as_user, payment_data):
    as_user.post(base_url, data=payment_data, expected_status=403)
