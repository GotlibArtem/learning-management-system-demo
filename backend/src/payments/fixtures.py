from typing import TYPE_CHECKING, Any

import pytest

from payments.models import Payment, PaymentInstrument, Recurrent
from products.models import Product
from users.models import User


if TYPE_CHECKING:
    from app.testing.factory import FixtureFactory


@pytest.fixture
def payment(factory: "FixtureFactory", user: User, product: Product, payment_instrument: PaymentInstrument, recurrent: Recurrent, **kwargs: Any) -> Payment:
    return factory.payment(
        user=user,
        product=product,
        payment_instrument=payment_instrument,
        recurrent=recurrent,
        **kwargs,
    )


@pytest.fixture
def payment_instrument(factory: "FixtureFactory", user: User) -> PaymentInstrument:
    return factory.payment_instrument(user=user)


@pytest.fixture
def recurrent(factory: "FixtureFactory", user: User, product: Product, payment_instrument: PaymentInstrument, **kwargs: Any) -> PaymentInstrument:
    return factory.recurrent(user=user, product=product, payment_instrument=payment_instrument, **kwargs)
