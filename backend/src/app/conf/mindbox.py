from app.conf.environ import env


MINDBOX_ENABLED = env("MINDBOX_ENABLED", cast=bool, default=True)
MINDBOX_URL = env("MINDBOX_URL", cast=str, default="https://api.mindbox.ru/v3/")
MINDBOX_ENDPOINT_ID = env("MINDBOX_ENDPOINT_ID", cast=str, default="")
MINDBOX_ENDPOINT_SECRET_KEY = env("MINDBOX_ENDPOINT_SECRET_KEY", cast=str)
