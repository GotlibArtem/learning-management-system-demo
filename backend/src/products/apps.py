from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class ProductsConfig(AppConfig):
    name = "products"
    verbose_name = _("Managing products")
