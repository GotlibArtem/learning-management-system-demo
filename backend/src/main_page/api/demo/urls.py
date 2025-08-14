from django.urls import include, path
from rest_framework.routers import SimpleRouter

from main_page.api.demo import viewsets


app_name = "main_page_content"

main_page_router = SimpleRouter()

main_page_router.register("recommendations", viewsets.MainPageRecommendationsViewSet)
main_page_router.register("content", viewsets.MainPageContentViewSet)
main_page_router.register("lecture-collections", viewsets.LectureBundleContentViewSet)
main_page_router.register("course-collections", viewsets.CourseBundleContentViewSet)

urlpatterns = [
    path("main-page/", include(main_page_router.urls)),
]
