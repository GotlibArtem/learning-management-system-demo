from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


app_name = "api_demo"

urlpatterns = [
    path("", include("main_page.api.demo.urls")),
    path("", include("mindbox.api.demo.urls")),
    path("", include("product_access.api.demo.urls")),
    path("auth/", include("a12n.api.urls")),
    path("users/", include("users.api.urls")),
    path("healthchecks/", include("django_healthchecks.urls")),
    path("bonuses/", include("bonuses.api.demo.urls")),
    path("payments/", include("payments.api.demo.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("docs/schema/", SpectacularAPIView.as_view(api_version="demo"), name="schema"),  # type: ignore
        path("docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema")),  # type: ignore
    ]
