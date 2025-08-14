from django.urls import path

from a12n.api import views


app_name = "a12n"

urlpatterns = [
    path("token/as/<str:user_id>/", views.TokenByUserId.as_view()),
    path("token/obtain-by-email/", views.TokenObtainByCodeView.as_view()),
    path("token/obtain-by-password/", views.TokenObtainByPasswordView.as_view()),
    path("token/refresh/", views.TokenRefreshView.as_view()),
    path("token/social/", views.TokenBySocialView.as_view()),
]
