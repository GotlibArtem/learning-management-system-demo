from django.urls import path

from users.api import viewsets


app_name = "users"


urlpatterns = [
    path("account/", viewsets.SelfView.as_view({"get": "get", "patch": "partial_update"})),
    path("account/bonuses/", viewsets.SelfView.as_view({"get": "bonuses"})),
    path("account/comment-token/", viewsets.SelfView.as_view({"get": "comment_auth"})),
    path("account/deactivate/", viewsets.SelfView.as_view({"post": "deactivate"})),
    path("auth/register/", viewsets.SignUpView.as_view()),
    path("auth/login/", viewsets.SignInView.as_view()),
    path("auth/social-register/", viewsets.SocialSignUpView.as_view()),
    path("billing/recurrent-info/", viewsets.UserRecurrentInfoView.as_view()),
]
