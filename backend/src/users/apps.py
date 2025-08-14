from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class UsersConfig(AppConfig):
    name = "users"
    verbose_name = _("Users")
