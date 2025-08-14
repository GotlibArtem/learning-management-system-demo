from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


api = [
    path("demo/", include("app.urls.demo", namespace="demo")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
    path("_nested_admin/", include("nested_admin.urls")),
    path("tech/api/demo/docs/schema/", SpectacularAPIView.as_view(api_version="demo"), name="schema"),
    path("tech/api/demo/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema")),
]
