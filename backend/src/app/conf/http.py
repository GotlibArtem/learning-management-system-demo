from app.conf.environ import env


ABSOLUTE_URL = env("ABSOLUTE_URL", cast=str)
BACKEND_APP_URL = env("BACKEND_APP_URL", cast=str)

DATA_UPLOAD_MAX_NUMBER_FIELDS = 2500

ALLOWED_HOSTS = ["*"]  # host validation is not necessary in 2020
