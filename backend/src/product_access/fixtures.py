import pytest
from faker import Faker

from app.testing.factory import FixtureFactory
from product_access.models import ProductAccess
from products.models import Product
from users.models import User


@pytest.fixture
def product_access(factory: FixtureFactory, product: Product, user: User, faker: Faker) -> ProductAccess:
    return factory.product_access(
        product=product,
        user=user,
        start_date=faker.past_date(),
        end_date=None,
    )
