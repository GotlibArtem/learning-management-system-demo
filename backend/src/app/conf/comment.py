from app.conf.environ import env


COMMENT_PROVIDER_API_KEY = env("COMMENT_PROVIDER_API_KEY", cast=str, default="")
