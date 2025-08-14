from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import Permission

from users.models import User


if TYPE_CHECKING:
    from app.testing.factory import FixtureFactory


@pytest.fixture
def user(factory: "FixtureFactory") -> User:
    return factory.user()


@pytest.fixture
def shop_user(factory: "FixtureFactory") -> User:
    """
    User for integration with the lms shop
    """
    user = factory.user()
    user.user_permissions.add(Permission.objects.get(codename="allow_shop_integration"))
    user.user_permissions.add(Permission.objects.get(codename="allow_bonuses_integration"))
    user.user_permissions.add(Permission.objects.get(codename="allow_marketing_integration"))
    user.user_permissions.add(Permission.objects.get(codename="allow_payment_integration"))
    user.user_permissions.add(Permission.objects.get(codename="allow_recurrent_integration"))
    return user


@pytest.fixture
def mindbox_user(factory: "FixtureFactory") -> User:
    """
    User for integration with mindbox
    """
    user = factory.user()
    user.user_permissions.add(Permission.objects.get(codename="allow_mindbox_integration"))
    return user
