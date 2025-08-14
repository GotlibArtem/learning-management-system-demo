import pytest

from product_access.services import PostCheckoutLinkGenerator


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.ABSOLUTE_URL = "https://the-frontend.lms.comx"


@pytest.fixture
def generator(product):
    return PostCheckoutLinkGenerator(
        username="jacksparrow@piratebay.com",
        code="7777",
        product=product,
    )


def test_link_with_code_is_generated(generator, product):
    expected_link = f"https://the-frontend.lms.comx/order-checkedout?email=jacksparrow%40piratebay.com&product_type={product.product_type}&product_id={product.id}&code=7777"

    assert generator() == expected_link


def test_link_without_code_is_generated(generator, product):
    generator.code = None

    expected_link = (
        f"https://the-frontend.lms.comx/order-checkedout?email=jacksparrow%40piratebay.com&product_type={product.product_type}&product_id={product.id}"
    )

    assert generator() == expected_link
