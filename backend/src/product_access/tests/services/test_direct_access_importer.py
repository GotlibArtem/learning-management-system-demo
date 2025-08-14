from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from product_access.models import ProductAccess
from product_access.services import DirectAccessImporter
from product_access.services.product_checkout_processor import ProductCheckoutProcessor


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def data():
    return {
        "orderId": "cm4wljl835r8g0119j2wsnpgh",
        "username": "some@gmail.test",
        "firstName": "Какой-то",
        "lastName": "Пользователь",
        "startDate": "2024-12-20",
        "shopId": "cm49wxvpf4sa00119jy6a9afe",
        "lmsId": "",
        "name": "О чём молчат картины: великие художники",
    }


@pytest.fixture
def importer(data):
    return DirectAccessImporter(data=data)


@pytest.fixture
def mock_checkout_processor(mocker):
    return mocker.spy(ProductCheckoutProcessor, "__call__")


def test_calling_product_checkout_processor(importer, mock_checkout_processor):
    importer()

    mock_checkout_processor.assert_called_once()
    checkout_event = mock_checkout_processor.call_args[0][0].checkout_event
    assert "event_id" in checkout_event
    assert checkout_event["event_type"] == "order-checkedout"
    assert "event_time" in checkout_event
    assert checkout_event["data"]["order_id"] == "cm4wljl835r8g0119j2wsnpgh"
    assert checkout_event["data"]["user"]["username"] == "some@gmail.test"
    assert checkout_event["data"]["user"]["first_name"] == "Какой-то"
    assert checkout_event["data"]["user"]["last_name"] == "Пользователь"
    assert checkout_event["data"]["start_date"] == date(2024, 12, 20)
    assert checkout_event["data"]["end_date"] is None
    assert checkout_event["data"]["product"]["shop_id"] == "cm49wxvpf4sa00119jy6a9afe"
    assert checkout_event["data"]["product"]["lms_id"] == ""
    assert checkout_event["data"]["product"]["name"] == "О чём молчат картины: великие художники"


@pytest.mark.parametrize("name", ["Подписка на 12 месяцев", "Подписка на 36 месяцев", "подписка на ", "Подписка  на 12 месяцев"])
def test_skip_subscription_access(importer, data, mock_checkout_processor, name):
    data["name"] = name

    importer()

    mock_checkout_processor.assert_not_called()


def test_setting_access_creation_time(importer):
    importer()

    access = ProductAccess.objects.get()
    assert access.created == datetime(2024, 1, 1, tzinfo=ZoneInfo("UTC"))


def test_import_is_idempotent(importer):
    importer()

    importer()

    assert ProductAccess.objects.count() == 1
