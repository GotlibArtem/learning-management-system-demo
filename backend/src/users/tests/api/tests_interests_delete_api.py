import pytest
from rest_framework import status


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/users/interests/"


def test_delete_interests(as_user, user, category):
    user.interests.add(category)

    as_user.delete(base_url, expected_status=status.HTTP_204_NO_CONTENT)

    user.refresh_from_db()
    assert user.interests.count() == 0


def test_delete_interests_when_empty(as_user, user):
    as_user.delete(base_url, expected_status=status.HTTP_204_NO_CONTENT)

    user.refresh_from_db()
    assert user.interests.count() == 0


def test_anon_forbidden(as_anon):
    as_anon.delete(base_url, expected_status=status.HTTP_401_UNAUTHORIZED)
