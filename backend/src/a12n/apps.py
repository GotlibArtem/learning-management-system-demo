from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class A12nConfig(AppConfig):
    name = "a12n"
    verbose_name = _("A12n")
