import pytest

from app.testing import ApiClient
from users.models import User


@pytest.fixture
def as_anon() -> ApiClient:
    return ApiClient()


@pytest.fixture
def as_user(user: User) -> ApiClient:
    return ApiClient(user=user)


@pytest.fixture
def as_shop_user(shop_user: User) -> ApiClient:
    return ApiClient(user=shop_user)


@pytest.fixture
def as_mindbox_user(mindbox_user: User) -> ApiClient:
    return ApiClient(user=mindbox_user)
