import pytest

from product_access.models import ProductAccess
from product_access.services import ProductAccessRevoker


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def revoker(product_access, make_dt):
    return ProductAccessRevoker(
        order_id=product_access.order_id,
        access_revoke_time=make_dt("2030-01-03"),
    )


@pytest.fixture
def ya_product_access(factory):
    return factory.product_access()


@pytest.mark.parametrize(
    ("field_to_update", "value"),
    [
        ("revoked_at", "2030-01-02"),
        ("granted_at", "2030-01-02"),
    ],
)
def test_access_is_revoked(revoker, product_access, make_dt, field_to_update, value):
    product_access.setattr_and_save(field_to_update, make_dt(value))

    revoker()

    product_access.refresh_from_db()
    assert product_access.revoked_at == make_dt("2030-01-03")


def test_access_of_other_order_is_preserved(revoker, ya_product_access):
    revoker()

    ya_product_access.refresh_from_db()
    assert ya_product_access.revoked_at is None


def test_revoke_if_current_revoke_time_is_not_set(revoker, product_access, make_dt):
    product_access.setattr_and_save("revoked_at", None)

    revoker()

    product_access.refresh_from_db()
    assert product_access.revoked_at == make_dt("2030-01-03")


def test_revoke_if_current_grant_time_is_not_set(revoker, product_access, make_dt):
    product_access.setattr_and_save("granted_at", None)

    revoker()

    product_access.refresh_from_db()
    assert product_access.revoked_at == make_dt("2030-01-03")


def test_skip_revoking_if_new_revoke_time_is_before_current_revoke_time(revoker, product_access, make_dt):
    product_access.setattr_and_save("revoked_at", make_dt("2030-01-04"))

    revoker()

    product_access.refresh_from_db()
    assert product_access.revoked_at == make_dt("2030-01-04")


def test_skip_updating_if_new_revoke_time_is_before_current_grant_time(revoker, product_access, make_dt):
    product_access.setattr_and_save("granted_at", make_dt("2030-01-04"))

    revoker()

    product_access.refresh_from_db()
    assert product_access.revoked_at is None


def test_create_revoked_access_if_access_is_not_exist(revoker, product_access, make_dt):
    product_access.delete()

    revoker()

    product_access = ProductAccess.objects.get()
    assert product_access.order_id == revoker.order_id
    assert product_access.user is None
    assert product_access.product is None
    assert product_access.granted_at is None
    assert product_access.revoked_at == make_dt("2030-01-03")
