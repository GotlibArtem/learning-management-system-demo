from datetime import date

import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/users/me/"


@pytest.fixture
def data():
    return {
        "firstName": "Honest",
        "lastName": "Abe",
        "birthdate": "1861-03-04",
        "avatarSlug": "abstract",
        "hasAcceptedDataConsent": True,
    }


def test_response(as_user, user, data):
    response = as_user.patch(base_url, data=data)

    user.refresh_from_db()
    assert response["id"] == str(user.pk)
    assert response["username"] == user.username
    assert response["firstName"] == user.first_name
    assert response["lastName"] == user.last_name
    assert response["birthdate"] == "1861-03-04"
    assert response["avatarSlug"] == user.avatar_slug
    assert response["remoteAddr"] == "127.0.0.1"
    assert response["hasAcceptedDataConsent"] is True
    assert response["hasRecurringSubscription"] is False
    assert response["subscriptionStartDate"] is None
    assert response["subscriptionEndDate"] is None
    assert set(response) == {
        "id",
        "username",
        "firstName",
        "lastName",
        "birthdate",
        "avatarSlug",
        "remoteAddr",
        "hasAcceptedDataConsent",
        "hasRecurringSubscription",
        "subscriptionStartDate",
        "subscriptionEndDate",
        "rhash",
    }


def test_user_actually_updated(as_user, user, data):
    as_user.patch(base_url, data=data)

    user.refresh_from_db()
    assert user.first_name == "Honest"
    assert user.last_name == "Abe"
    assert user.birthdate == date(1861, 3, 4)
    assert user.avatar_slug == "abstract"
    assert user.has_accepted_data_consent is True


def test_partial_update(as_user, user):
    as_user.patch(base_url, data={"firstName": "Honest", "hasAcceptedDataConsent": False})

    user.refresh_from_db()
    assert user.first_name == "Honest"
    assert user.has_accepted_data_consent is False


def test_avatar_validation(as_user, data):
    data["avatarSlug"] = "invalid"

    as_user.patch(base_url, data=data, expected_status=400)
