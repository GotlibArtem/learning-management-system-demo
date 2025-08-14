from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class BonusesConfig(AppConfig):
    name = "bonuses"
    verbose_name = _("Users - Bonuses")
