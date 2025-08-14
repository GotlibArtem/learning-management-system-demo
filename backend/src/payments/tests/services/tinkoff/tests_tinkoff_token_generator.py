import hashlib

import pytest

from payments.services.tinkoff.tinkoff_token_generator import TinkoffTokenGenerator


pytestmark = [
    pytest.mark.django_db,
]


def test_token_generator(monkeypatch, settings):
    settings.TINKOFF_TERMINAL_PASSWORD = "testpass"
    payload = {
        "TerminalKey": "123456",
        "OrderId": "order-001",
        "Amount": "1800000",
    }

    flat_fields = {k: v for k, v in payload.items() if isinstance(v, str | int | float) and v is not None}
    flat_fields["Password"] = settings.TINKOFF_TERMINAL_PASSWORD
    token_str = "".join(str(value) for _, value in sorted(flat_fields.items()))
    expected = hashlib.sha256(token_str.encode("utf-8")).hexdigest()

    token = TinkoffTokenGenerator(payload=payload)()

    assert token == expected


def test_token_generator_filters_non_str_int_float(monkeypatch, settings):
    settings.TINKOFF_TERMINAL_PASSWORD = "testpass"
    payload = {
        "TerminalKey": "123456",
        "OrderId": "order-001",
        "Amount": "1800000",
        "Description": "Подписка на 12 месяцев",
        "Taxation": settings.TINKOFF_TAXATION,
    }

    flat_fields = {k: v for k, v in payload.items() if isinstance(v, str | int | float) and v is not None}
    flat_fields["Password"] = settings.TINKOFF_TERMINAL_PASSWORD
    token_str = "".join(str(value) for _, value in sorted(flat_fields.items()))
    expected = hashlib.sha256(token_str.encode("utf-8")).hexdigest()

    token = TinkoffTokenGenerator(payload=payload)()

    assert token == expected
