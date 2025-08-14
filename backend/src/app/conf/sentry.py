from app.conf.environ import env


# Sentry
# https://sentry.io/for/django/

SENTRY_DSN = env("SENTRY_DSN", cast=str, default="")

if not env("DEBUG") and len(SENTRY_DSN):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    def strip_transactions(event, hint):  # type: ignore[no-untyped-def]
        del hint

        if event["transaction"] in (
            "/api/v2/healthchecks/{service}/",
            "/api/v2/users/me/",
            "/admin/jsi18n/",
            "/static/admin/",
        ):
            return None

        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.05,
        send_default_pii=True,
        profiles_sample_rate=0.05,
        before_send_transaction=strip_transactions,
    )
