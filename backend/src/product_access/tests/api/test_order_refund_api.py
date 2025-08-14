from contextlib import suppress
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.models import ShopDeadLetter


pytestmark = [
    pytest.mark.django_db,
    pytest.mark.freeze_time("2049-01-05 10:00:00"),
]


base_url = "/api/demo/order-refund/"


@pytest.fixture
def processing_error(mocker):
    return mocker.patch(
        "product_access.services.ProductAccessRevoker.__call__",
        side_effect=Exception("unexpected error"),
    )


def test_access_is_revoked(as_shop_user, refund_data, product_access):
    as_shop_user.post(base_url, data=refund_data, expected_status=200)

    product_access.refresh_from_db()
    assert product_access.revoked_at is not None


def test_400_for_invalid_data(as_shop_user, refund_data):
    refund_data["event_time"] = "invalid time"

    as_shop_user.post(base_url, data=refund_data, expected_status=400)


@pytest.mark.usefixtures("processing_error")
def test_dead_letter_is_created_on_any_error(as_shop_user, refund_data):
    with suppress(Exception):
        as_shop_user.post(base_url, data=refund_data)

    letter = ShopDeadLetter.objects.get()
    assert letter.event_type == "order-refunded"
    assert letter.raw_data is not None
    assert letter.details.startswith("Traceback (most recent call last)")


def test_revoked_at_stored_correctly_with_utc(as_shop_user, refund_data, product_access):
    utc_now = datetime.now(ZoneInfo("UTC"))
    refund_data["eventTime"] = utc_now.isoformat()

    as_shop_user.post(base_url, data=refund_data, expected_status=200)

    product_access.refresh_from_db()
    assert product_access.revoked_at.utcoffset().total_seconds() == 0


@pytest.mark.parametrize(
    "timezone",
    [
        "America/New_York",
        "Asia/Tokyo",
        "Europe/London",
    ],
)
def test_revoked_at_converts_different_timezones_to_utc(
    as_shop_user,
    refund_data_with_tz,
    product_access,
    timezone,
):
    data = refund_data_with_tz(timezone)
    event_time = datetime.fromisoformat(data["eventTime"])

    as_shop_user.post(base_url, data=data, expected_status=200)

    product_access.refresh_from_db()
    assert product_access.revoked_at is not None
    event_time_utc = event_time.astimezone(ZoneInfo("UTC"))
    assert (product_access.revoked_at - event_time_utc).total_seconds() == 0
    assert product_access.revoked_at.utcoffset().total_seconds() == 0
