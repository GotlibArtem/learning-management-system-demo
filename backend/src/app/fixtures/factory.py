import pytest
from django.utils import translation

from app.testing.factory import FixtureFactory


@pytest.fixture
def factory() -> FixtureFactory:
    return FixtureFactory()


@pytest.fixture(autouse=True)
def en():  # type: ignore
    with translation.override("en"):
        yield
