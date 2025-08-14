from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class PaymentsConfig(AppConfig):
    name = "payments"
    verbose_name = _("Managing payments")
