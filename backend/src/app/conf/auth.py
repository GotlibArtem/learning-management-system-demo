from datetime import timedelta

from app.conf.environ import env


AUTH_USER_MODEL = "users.User"
AXES_ENABLED = env("AXES_ENABLED", cast=bool, default=True)
AXES_LOCKOUT_PARAMETERS = ["ip_address", ["username", "user_agent"]]
AXES_COOLOFF_TIME = 1  # 1 hour
AXES_FAILURE_LIMIT = 10
AXES_RESET_ON_SUCCESS = True

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend",
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.yandex.YaruOAuth2",
    "social_core.backends.mailru.MRGOAuth2",
    "social_core.backends.apple.AppleIdAuth",
    "django.contrib.auth.backends.ModelBackend",
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("GOOGLE_OAUTH_ID", cast=str, default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("GOOGLE_OAUTH_SECRET", cast=str, default="")
SOCIAL_AUTH_YARU_KEY = env("YA_OAUTH_ID", cast=str, default="")
SOCIAL_AUTH_YARU_SECRET = env("YA_OAUTH_SECRET", cast=str, default="")
SOCIAL_AUTH_MAILRU_KEY = env("MAILRU_OAUTH_ID", cast=str, default="")
SOCIAL_AUTH_MAILRU_SECRET = env("MAILRU_OAUTH_SECRET", cast=str, default="")
SOCIAL_AUTH_APPLE_ID_CLIENT = env("APPLE_ID_CLIENT", cast=str, default="")
SOCIAL_AUTH_APPLE_ID_TEAM = env("APPLE_ID_TEAM", cast=str, default="")
SOCIAL_AUTH_APPLE_ID_KEY = env("APPLE_ID_KEY", cast=str, default="")
SOCIAL_AUTH_APPLE_ID_SECRET = env.str("APPLE_ID_SECRET", multiline=True, default="")
SOCIAL_AUTH_APPLE_ID_SCOPE = ["email", "name"]
SOCIAL_AUTH_APPLE_ID_EMAIL_AS_USERNAME = True

SOCIAL_AUTH_PROVIDERS = {
    "google-oauth2": {
        "auth_scheme": "Bearer",
        "client_id": SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        "client_secret": SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
        "token_url": env("GOOGLE_OAUTH_TOKEN_URL", cast=str, default="https://oauth2.googleapis.com/token"),
        "userinfo_url": env("GOOGLE_OAUTH_USERINFO_URL", cast=str, default="https://openidconnect.googleapis.com/demo/userinfo"),
    },
    "yaru": {
        "auth_scheme": "OAuth",
        "client_id": SOCIAL_AUTH_YARU_KEY,
        "client_secret": SOCIAL_AUTH_YARU_SECRET,
        "token_url": env("YA_OAUTH_TOKEN_URL", cast=str, default="https://oauth.yandex.ru/token"),
        "userinfo_url": env("YA_OAUTH_USERINFO_URL", cast=str, default="https://login.yandex.ru/info"),
    },
    "mailru": {
        "auth_scheme": "Bearer",
        "client_id": SOCIAL_AUTH_MAILRU_KEY,
        "client_secret": SOCIAL_AUTH_MAILRU_SECRET,
        "token_url": env("MAILRU_OAUTH_TOKEN_URL", cast=str, default="https://oauth.mail.ru/token"),
        "userinfo_url": env("MAILRU_OAUTH_USERINFO_URL", cast=str, default="https://oauth.mail.ru/userinfo"),
    },
    "apple-id": {
        "auth_scheme": "Bearer",
        "client_id": SOCIAL_AUTH_APPLE_ID_CLIENT,
        "client_secret": SOCIAL_AUTH_APPLE_ID_SECRET,
        "token_url": env("APPLE_ID_TOKEN_URL", cast=str, default="https://appleid.apple.com/auth/token"),
        "userinfo_url": None,
    },
}

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "users.pipeline.associate_by_email",
    "social_core.pipeline.social_auth.associate_user",
)

SIMPLE_JWT = {
    "SLIDING_TOKEN_LIFETIME": timedelta(days=365),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=3 * 365),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.SlidingToken",),
    "ALGORITHM": "RS256",
    "SIGNING_KEY": env.str("JWT_PRIVATE_KEY", multiline=True),
    "VERIFYING_KEY": env.str("JWT_PUBLIC_KEY", multiline=True),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

PASSWORDLESS_EMAIL_CODE_LENGTH = 4
PASSWORDLESS_EMAIL_CODE_EXPIRATION_TIME = timedelta(minutes=20)

#
# Security notice: we use plain bcrypt to store passwords.
#
# We avoid django default pre-hashing algorithm
# from contrib.auth.hashers.BCryptSHA256PasswordHasher.
#
# The reason is compatibility with other hashing libraries, like
# Ruby Devise or Laravel default hashing algorithm.
#
# This means we can't store passwords longer then 72 symbols.
#

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]
