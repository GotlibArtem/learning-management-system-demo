# Application definition

APPS = [
    "a12n.apps.A12nConfig",
    "app.apps.AppConfig",
    "bonuses.apps.BonusesConfig",
    "main_page.apps.MainPageContentConfig",
    "mindbox.apps.MindboxConfig",
    "payments.apps.PaymentsConfig",
    "product_access.apps.ProductAccessConfig",
    "products.apps.ProductsConfig",
    "users.apps.UsersConfig",
]

THIRD_PARTY_APPS = [
    "axes",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "cachalot",
    "ckeditor",
    "nested_admin",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "rest_social_auth",
    "social_django",
]

INSTALLED_APPS = APPS + THIRD_PARTY_APPS
