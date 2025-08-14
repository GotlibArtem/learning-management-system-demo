from django.urls import path

from bonuses.api.demo import views


app_name = "bonuses"

urlpatterns = [
    path("account/", views.BonusAccountByEmailView.as_view(), name="bonus-account-by-email"),
    path("earn/", views.BonusEarnView.as_view(), name="bonus-earn"),
    path("spend/", views.BonusSpendView.as_view(), name="bonus-spend"),
]
