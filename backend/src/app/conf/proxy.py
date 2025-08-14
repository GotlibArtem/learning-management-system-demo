from app.conf.environ import env


# Proxy configuration for external API integrations
PROXY_URL = env("PROXY_URL", cast=str, default="")
PROXY_TIMEOUT = env("PROXY_TIMEOUT", cast=int, default=30)
PROXY_VERIFY_SSL = env("PROXY_VERIFY_SSL", cast=bool, default=True)
