from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from product_access.models import ProductAccess
from product_access.services import TimedProductAccessProvider


msk = ZoneInfo("Europe/Moscow")


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(params=[datetime(2030, 4, 3, 23, 59, 59, 999999, tzinfo=msk), None])
def end_at(request):
    return request.param


@pytest.fixture
def provider(user, product, end_at, make_dt):
    return TimedProductAccessProvider(
        user=user,
        product=product,
        start_at=datetime(2030, 1, 1, 12, 0, 0, 0, tzinfo=msk),
        end_at=end_at,
        order_id="some-id",
        access_granted_time=make_dt("2030-01-03"),
    )


@pytest.fixture
def product_access(factory, make_dt):
    return factory.product_access(
        user=factory.user(),
        product=factory.product(),
        order_id="some-id",
        granted_at=make_dt("2030-01-02"),
    )


@pytest.fixture
def empty_access(factory, make_dt):
    return factory.product_access(
        order_id="some-id",
        revoked_at=make_dt("2030-04-01"),
    )


def test_access_is_granted(provider, end_at, user, product, make_dt):
    provider()

    access = ProductAccess.objects.get()

    assert access.user == user
    assert access.product == product
    assert access.start_date == datetime(2030, 1, 1, 12, 0, 0, 0, tzinfo=msk)
    assert access.end_date == end_at
    assert access.order_id == "some-id"
    assert access.granted_at == make_dt("2030-01-03")


def test_idempotency_of_access_granting(provider):
    provider()
    provider()

    assert ProductAccess.objects.count() == 1


def test_update_existing_access_by_order_id(provider, product_access, end_at, user, product):
    provider()

    product_access.refresh_from_db()

    assert product_access.user == user
    assert product_access.product == product
    assert product_access.start_date == datetime(2030, 1, 1, 12, 0, 0, 0, tzinfo=msk)
    assert product_access.end_date == end_at


def test_reset_revoke_time_after_access_granting(provider, product_access, make_dt):
    product_access.setattr_and_save("revoked_at", make_dt("2030-01-01"))

    provider()

    product_access.refresh_from_db()

    assert product_access.revoked_at is None


def test_skip_updating_if_new_grant_time_is_before_current_grant_time(provider, product_access, make_dt):
    product_access.setattr_and_save("granted_at", make_dt("2030-01-04"))

    provider()

    product_access.refresh_from_db()

    assert product_access.granted_at == make_dt("2030-01-04")


def test_skip_updating_if_new_grant_time_is_before_current_revoke_time(provider, product_access, make_dt):
    product_access.setattr_and_save("revoked_at", make_dt("2030-01-04"))

    provider()

    product_access.refresh_from_db()

    assert product_access.granted_at == make_dt("2030-01-02")


def test_update_if_current_revoke_time_is_not_set(provider, product_access, make_dt):
    product_access.setattr_and_save("revoked_at", None)

    provider()

    product_access.refresh_from_db()

    assert product_access.granted_at == make_dt("2030-01-03")


def test_update_if_current_grant_time_is_not_set(provider, product_access, make_dt):
    product_access.setattr_and_save("granted_at", None)

    provider()

    product_access.refresh_from_db()

    assert product_access.granted_at == make_dt("2030-01-03")


def test_empty_access_is_filled_in_in_any_case(provider, empty_access, user, product, end_at, make_dt):
    provider()

    empty_access.refresh_from_db()

    assert empty_access.user == user
    assert empty_access.product == product
    assert empty_access.start_date == datetime(2030, 1, 1, 12, 0, 0, 0, tzinfo=msk)
    assert empty_access.end_date == end_at
    assert empty_access.granted_at == make_dt("2030-01-03")
    assert empty_access.revoked_at == make_dt("2030-04-01")
