from app.conf.environ import env


CACHALOT_ENABLED = env("CACHALOT_ENABLED", cast=bool, default=False)
CACHE_ENABLED = CACHALOT_ENABLED
CACHE_DURATION_SECONDS = env("CACHE_DURATION_SECONDS", cast=int, default=60 * 5)

if CACHALOT_ENABLED:
    CACHES = {
        "default": env.cache("CACHE_URL", default="redis://localhost:6379/1"),
    }

CACHALOT_UNCACHABLE_TABLES = frozenset(
    (
        "django_migrations",
        "django_content_type",
    ),
)
