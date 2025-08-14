import pytest
from rest_framework import status


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/bonuses/earn/"


def test_earn_bonuses(as_shop_user, user):
    data = {"email": user.email, "amount": 50, "reason": "test earn"}
    response = as_shop_user.post(base_url, data=data, expected_status=status.HTTP_201_CREATED)

    assert response["email"] == user.email
    assert response["balance"] == 50
    assert response["isActive"] is True


def test_400_for_invalid_amount(as_shop_user, user):
    data = {"email": user.email, "amount": 0, "reason": "test"}
    response = as_shop_user.post(base_url, data=data, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "amount" in response
    assert any("positive" in str(msg) or "greater than or equal to 1" in str(msg) for msg in response["amount"])


def test_for_nonexistent_user(as_shop_user):
    data = {"email": "notfound@example.com", "amount": 10, "reason": "test"}
    response = as_shop_user.post(base_url, data=data, expected_status=status.HTTP_201_CREATED)

    assert response["email"] == "notfound@example.com"
    assert response["balance"] == 10
    assert response["isActive"] is True


def test_400_for_missing_fields(as_shop_user):
    response = as_shop_user.post(base_url, data={}, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "email" in response
    assert "amount" in response


def test_forbid_for_anon(as_anon, user):
    data = {"email": user.email, "amount": 10, "reason": "test"}
    as_anon.post(base_url, data=data, expected_status=status.HTTP_401_UNAUTHORIZED)
