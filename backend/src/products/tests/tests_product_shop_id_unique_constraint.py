from contextlib import nullcontext as do_not_raise

import pytest
from django.db import IntegrityError


pytestmark = [
    pytest.mark.django_db,
]


@pytest.mark.usefixtures("product")
def test_forbid_not_unique_shop_id(factory):
    factory.product(shop_id="0")

    with pytest.raises(IntegrityError):
        factory.product(shop_id="0")


def test_allow_duplicates_of_empty_shop_id(factory):
    factory.product(shop_id="")

    with do_not_raise():
        factory.product(shop_id="")
