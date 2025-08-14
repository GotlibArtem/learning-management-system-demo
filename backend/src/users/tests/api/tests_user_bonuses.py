import pytest


pytestmark = [pytest.mark.django_db]

base_url = "/api/demo/users/me/bonuses/"


def test_response(as_user):
    response = as_user.get(base_url)

    assert response == {"bonuses": 0}


def test_forbid_for_anon(as_anon):
    as_anon.get(base_url, expected_status=401)
