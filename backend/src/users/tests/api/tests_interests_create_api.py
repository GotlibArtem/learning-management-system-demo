import pytest
from rest_framework import status


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/users/interests/"


@pytest.fixture
def categories(factory):
    return [
        factory.category(slug="art"),
        factory.category(slug="cinema"),
        factory.category(slug="music"),
    ]


def test_set_interests(as_user, user, categories):
    got = as_user.post(base_url, data={"interests": ["art", "cinema"]}, expected_status=status.HTTP_200_OK)

    user.refresh_from_db()

    assert set(got["interests"]) == {"art", "cinema"}
    assert set(user.interests.slugs()) == {"art", "cinema"}


def test_overwrite_previous_interests(as_user, user, categories):
    user.interests.add(categories[0])

    as_user.post(base_url, data={"interests": ["cinema"]}, expected_status=status.HTTP_200_OK)

    user.refresh_from_db()

    assert user.interests.slugs() == ["cinema"]


def test_return_updated_interests(as_user, categories):
    got = as_user.post(base_url, data={"interests": ["art", "music"]}, expected_status=status.HTTP_200_OK)

    assert set(got["interests"]) == {"art", "music"}


def test_invalid_slug_returns_400(as_user):
    as_user.post(base_url, data={"interests": ["nonexistent"]}, expected_status=status.HTTP_400_BAD_REQUEST)


def test_anon_forbidden(as_anon):
    as_anon.post(base_url, data={"interests": ["art"]}, expected_status=status.HTTP_401_UNAUTHORIZED)
