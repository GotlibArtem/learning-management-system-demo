from django.utils.translation import gettext_lazy as _

from main_page.models.main_page_content import CATEGORIES_CONTENT_REF, MainPageContent
from main_page.models.mixins import MainPageContentParentLinkMixin


class CategoriesContent(MainPageContentParentLinkMixin, MainPageContent):  # type: ignore
    """Here may be more complex configuration of categories on main page."""

    _main_page_content_type: str = CATEGORIES_CONTENT_REF

    class Meta:
        verbose_name = _("Categories content item")
        verbose_name_plural = _("Categories content list")
        ordering = ["position_on_page", "created"]
