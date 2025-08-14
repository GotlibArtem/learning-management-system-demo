from django.utils.translation import gettext_lazy as _

from app.base_config import AppConfig


class MainPageContentConfig(AppConfig):
    name = "main_page"
    verbose_name = _("Main page")
