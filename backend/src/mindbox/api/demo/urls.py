from django.urls import path

from mindbox.api.demo import views


app_name = "mindbox"

urlpatterns = [
    path("mindbox/post-checkout-magic-link/", views.MindboxPostCheckoutMagicLinkView.as_view()),
]
