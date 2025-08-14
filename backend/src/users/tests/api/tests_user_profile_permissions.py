import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/users/me/"


def test_forbid_for_anon(as_anon):
    as_anon.get(base_url, expected_status=401)
