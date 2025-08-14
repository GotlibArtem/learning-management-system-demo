from django.urls import path

from product_access.api.demo import views


app_name = "product_access"

urlpatterns = [
    path("checkout/", views.OrderCheckoutView.as_view()),
    path("refund/", views.OrderRefundView.as_view()),
    path("promo-access/", views.PromoAccessView.as_view()),
]
