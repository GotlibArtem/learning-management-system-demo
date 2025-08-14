from datetime import datetime

import pytest


@pytest.fixture
def payment_data(user, product):
    return {
        "payment_id": "ext-123",
        "order_id": "order-456",
        "user": {
            "email": user.username,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "product": {
            "lms_id": product.id,
            "shop_id": "shop-789",
            "name": product.name,
        },
        "source": "SITE",
        "provider": "TINKOFF",
        "payment_method": "CARD",
        "status": "PAID",
        "paid_at": datetime(2030, 1, 1, 12, 0),
        "order_price": float(100),
        "total_price": float(90),
        "discount_price": float(10),
        "bonus_applied": float(0),
        "is_recurrent": False,
        "provider_response": {},
    }


@pytest.fixture
def recurrent_data():
    return {
        "status": "ACTIVE",
        "charge_token": "token-123",
        "charge_method": "CARD",
        "provider": "TINKOFF",
        "amount": float(90),
        "next_charge_date": datetime(2030, 2, 1, 12, 0),
        "last_attempt_charge_date": None,
        "last_attempt_charge_status": None,
        "attempts_charge": [
            {
                "pan": "**** 1234",
                "token": "secure-token",
                "amount": "90",
                "currency": "rub",
                "card_id": "card-xyz",
                "success": True,
                "exp_date": "12/30",
                "rebill_id": "rebill-abc123",
                "error_code": "0",
                "payment_id": "ext-123",
            },
        ],
        "attempts_charge_raw": [
            {},
        ],
    }


@pytest.fixture(autouse=True)
def mock_tinkoff_post(monkeypatch):
    class MockResponse:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    def mock_post(url, *args, **kwargs):
        if url.endswith("/Charge"):
            return MockResponse(
                {
                    "TerminalKey": "TinkoffBankTest",
                    "Amount": 100000,
                    "OrderId": "21050",
                    "Success": True,
                    "Status": "CONFIRMED",
                    "PaymentId": "13660",
                    "ErrorCode": "0",
                },
            )
        if url.endswith("/Init"):
            return MockResponse(
                {
                    "Success": True,
                    "ErrorCode": "0",
                    "TerminalKey": "TinkoffBankTest",
                    "Status": "NEW",
                    "PaymentId": "3093639567",
                    "OrderId": "21090",
                    "Amount": 140000,
                    "PaymentURL": "https://securepay.tinkoff.ru/new/fU1ppgqa",
                },
            )
        return MockResponse({})

    monkeypatch.setattr("requests.post", mock_post)
