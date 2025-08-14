import pytest

from users.services import UserDeactivator, UserDeactivatorException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def active_user(user):
    user.is_active = True
    user.save()

    return user


@pytest.fixture
def inactive_user(user):
    user.is_active = False
    user.save()

    return user


def test_user_is_deactivated(active_user):
    assert active_user.is_active is True

    UserDeactivator(user=active_user)()
    active_user.refresh_from_db()

    assert active_user.is_active is False


def test_raises_if_user_already_deactivated(inactive_user):
    with pytest.raises(UserDeactivatorException, match="User is already deactivated"):
        UserDeactivator(user=inactive_user)()
