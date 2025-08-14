from app.conf.environ import env


TINKOFF_API_URL = env("TINKOFF_API_URL", cast=str, default="https://rest-api-test.tinkoff.ru/v2")
TINKOFF_TERMINAL_KEY = env("TINKOFF_TERMINAL_KEY", cast=str, default="")
TINKOFF_TERMINAL_PASSWORD = env("TINKOFF_TERMINAL_PASSWORD", cast=str, default="")
TINKOFF_TAXATION = env("TINKOFF_TAXATION", cast=str, default="")
TINKOFF_TAX = env("TINKOFF_TAX", cast=str, default="")
TINKOFF_PAYMENT_OBJECT = env("TINKOFF_PAYMENT_OBJECT", cast=str, default="")
