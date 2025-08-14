import pytest
from django.contrib.auth.models import Permission

from a12n.models import PasswordlessEmailAuthCode


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/mindbox/post-checkout-magic-link/"


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.ABSOLUTE_URL = "https://the-frontend.lms.comx"


@pytest.fixture
def data():
    return {
        "email": "varya@gemail.comx",
    }


def test_response(as_mindbox_user, data):
    response = as_mindbox_user.post(base_url, data=data, expected_status=200)

    code = PasswordlessEmailAuthCode.objects.get().code
    assert response["authenticationLink"] == f"https://the-frontend.lms.comx/product-checkedout/?email=varya%40gemail.comx&code={code}"
    assert set(response) == {"authenticationLink"}


def test_400_for_invalid_data(as_mindbox_user, data):
    data["email"] = "invalid email"

    as_mindbox_user.post(base_url, data=data, expected_status=400)


def test_forbid_without_necessary_permissions(as_mindbox_user, data):
    required_permission = Permission.objects.get(codename="allow_mindbox_integration")
    as_mindbox_user.user.user_permissions.remove(required_permission)

    as_mindbox_user.post(base_url, data=data, expected_status=403)


def test_forbid_for_anon(as_anon, data):
    as_anon.post(base_url, data=data, expected_status=401)


def test_forbid_for_lms_user(as_user, data):
    as_user.post(base_url, data=data, expected_status=403)
