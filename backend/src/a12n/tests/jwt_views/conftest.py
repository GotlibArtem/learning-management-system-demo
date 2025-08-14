import pytest
from freezegun import freeze_time
from rest_framework_simplejwt.tokens import SlidingToken


@pytest.fixture(autouse=True)
def _enable_django_axes(settings):
    settings.AXES_ENABLED = True


@pytest.fixture(autouse=True)
def user(factory):
    user = factory.user(username="borisjohnson@mi6.uk")
    user.set_password("sn00pd0g")
    user.save()

    return user


@pytest.fixture
def initial_token(user):
    with freeze_time("2049-01-05 10:20"):
        token = SlidingToken.for_user(user)
        return str(token)
