from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from product_access.models import ProductAccess
from product_access.services import SubscriptionAccessImporter


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def data():
    return {
        "Имя": "Ванесса",
        "Фамилия": "Мэй",
        "E-mail": "vm@gmail.test",
        "Телефон": None,
        "Дата регистрации": "2024-12-12T13:39:58.000Z",
        "Последний день подписки": "2025-12-12T12:41:05.187Z",
        "Реф.код": "33SS01",
    }


@pytest.fixture
def importer(data, product):
    return SubscriptionAccessImporter(data=data, product=product)


@pytest.fixture(autouse=True)
def user(factory):
    return factory.user(username="vm@gmail.test")


@pytest.fixture
def access(factory, user, product):
    return factory.product_access(user=user, product=product)


def test_product_access_is_created(importer, user, product, make_dt):
    importer()

    access = ProductAccess.objects.get()
    assert access.user == user
    assert access.product == product
    assert access.start_date == datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=msk)
    assert access.end_date == datetime(2025, 12, 12, 23, 59, 59, 999999, tzinfo=msk)
    assert access.order_id != ""
    assert access.granted_at == make_dt("2024-01-01")
    assert access.revoked_at is None


def test_existing_access_is_updated(importer, user, product, access, make_dt):
    importer()

    access.refresh_from_db()
    assert access.user == user
    assert access.product == product
    assert access.start_date == datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=msk)
    assert access.end_date == datetime(2025, 12, 12, 23, 59, 59, 999999, tzinfo=msk)
    assert access.granted_at == make_dt("2024-01-01")
    assert access.revoked_at is None


def test_skip_users_with_no_subscription(importer, data):
    data["Последний день подписки"] = ""

    importer()

    assert ProductAccess.objects.count() == 0
