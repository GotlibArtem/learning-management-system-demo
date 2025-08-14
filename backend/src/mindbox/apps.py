from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class MindboxConfig(AppConfig):
    name = "mindbox"
    verbose_name = _("Mindbox")
