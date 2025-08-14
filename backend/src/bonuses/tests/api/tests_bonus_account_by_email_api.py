import pytest
from rest_framework import status


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/bonuses/account/"


def test_get_bonus_account_by_email(as_shop_user, bonus_account):
    response = as_shop_user.get(base_url, data={"email": bonus_account.user.email}, expected_status=status.HTTP_200_OK)

    assert response["email"] == bonus_account.user.email
    assert response["balance"] == bonus_account.balance
    assert response["isActive"] is True


def test_400_for_nonexistent_user(as_shop_user):
    response = as_shop_user.get(base_url, data={"email": "notfound@example.com"}, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "User matching query does not exist." in response["serviceError"]


def test_400_for_inactive_account(as_shop_user, bonus_account):
    bonus_account.is_active = False
    bonus_account.save()
    response = as_shop_user.get(base_url, data={"email": bonus_account.user.email}, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "Bonus account is not active." in response["serviceError"]


def test_400_for_missing_fields(as_shop_user):
    response = as_shop_user.get(base_url, expected_status=status.HTTP_400_BAD_REQUEST)

    assert "email" in response


def test_forbid_for_anon(as_anon, bonus_account):
    as_anon.get(base_url, data={"email": bonus_account.user.email}, expected_status=status.HTTP_401_UNAUTHORIZED)
