import pytest

from app.testing.factory import FixtureFactory
from products.models import Product


@pytest.fixture
def product(factory: FixtureFactory) -> Product:
    return factory.product()
