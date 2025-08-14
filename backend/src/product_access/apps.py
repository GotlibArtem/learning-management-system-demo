from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class ProductAccessConfig(AppConfig):
    name = "product_access"
    verbose_name = _("Managing product access entries")
