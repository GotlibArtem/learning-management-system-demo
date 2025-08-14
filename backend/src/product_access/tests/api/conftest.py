import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest


@pytest.fixture
def checkout_data(user, product):
    return {
        "eventId": str(uuid.uuid4()),
        "eventType": "order-checkedout",
        "eventTime": datetime.now().isoformat(),
        "data": {
            "orderId": str(uuid.uuid4()),
            "user": {
                "username": user.username,
                "firstName": user.first_name,
                "lastName": user.last_name,
            },
            "startDate": "2000-01-01",
            "endDate": "2000-02-01",
            "product": {
                "lmsId": str(product.id),
                "shopId": product.shop_id,
                "name": product.name,
            },
        },
    }


@pytest.fixture
def refund_data(product_access):
    return {
        "eventId": str(uuid.uuid4()),
        "eventType": "order-checkedout",
        "eventTime": datetime.now().isoformat(),
        "data": {
            "orderId": product_access.order_id,
        },
    }


@pytest.fixture
def refund_data_with_tz(refund_data):
    def _refund_data_with_tz(timezone: str) -> dict:
        data = refund_data.copy()
        dt = datetime.now(ZoneInfo(timezone))
        data["eventTime"] = dt.isoformat()
        return data

    return _refund_data_with_tz
