import pytest
from django.contrib.auth.models import Permission


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/order-refund/"


def test_forbid_without_necessary_permissions(as_shop_user, checkout_data):
    required_permission = Permission.objects.get(codename="allow_shop_integration")
    as_shop_user.user.user_permissions.remove(required_permission)

    as_shop_user.post(base_url, data=checkout_data, expected_status=403)


def test_forbid_for_anon(as_anon, checkout_data):
    as_anon.post(base_url, data=checkout_data, expected_status=401)


def test_forbid_for_lms_user(as_user, checkout_data):
    as_user.post(base_url, data=checkout_data, expected_status=403)
