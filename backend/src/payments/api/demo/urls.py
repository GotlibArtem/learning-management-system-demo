from django.urls import path

from payments.api.demo import views


app_name = "payments"


urlpatterns = [
    path("from-shop/", views.PaymentFromShopView.as_view()),
]
