import pytest
from rest_framework import status


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/bonuses/spend/"


def test_spend_bonuses(as_shop_user, bonus_account):
    data = {"email": bonus_account.user.email, "amount": 10, "reason": "test spend"}
    response = as_shop_user.post(base_url, data=data, expected_status=status.HTTP_201_CREATED)

    assert response["email"] == bonus_account.user.email
    assert response["balance"] == bonus_account.balance - 10
    assert response["isActive"] is True


def test_raises_if_not_enough_balance(as_shop_user, bonus_account):
    data = {"email": bonus_account.user.email, "amount": bonus_account.balance + 1, "reason": "test fail"}
    response = as_shop_user.post(base_url, data=data, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "Insufficient bonus balance." in response["serviceError"]


def test_400_for_nonexistent_user(as_shop_user):
    data = {"email": "notfound@example.com", "amount": 10, "reason": "test"}
    response = as_shop_user.post(base_url, data=data, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "User matching query does not exist." in response["serviceError"]


def test_raises_if_account_inactive(as_shop_user, bonus_account):
    bonus_account.is_active = False
    bonus_account.save()

    data = {"email": bonus_account.user.email, "amount": 10, "reason": "test"}
    response = as_shop_user.post(base_url, data=data, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "Bonus account is not active." in response["serviceError"]


def test_400_for_missing_fields(as_shop_user):
    response = as_shop_user.post(base_url, data={}, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "email" in response
    assert "amount" in response


def test_forbid_for_anon(as_anon, bonus_account):
    data = {"email": bonus_account.user.email, "amount": 10, "reason": "test"}
    as_anon.post(base_url, data=data, expected_status=status.HTTP_401_UNAUTHORIZED)
