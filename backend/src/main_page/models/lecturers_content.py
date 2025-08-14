from django.utils.translation import gettext_lazy as _

from main_page.models.main_page_content import LECTURERS_CONTENT_REF, MainPageContent
from main_page.models.mixins import MainPageContentParentLinkMixin


class LecturersContent(MainPageContentParentLinkMixin, MainPageContent):  # type: ignore
    """Here may be more complex configuration of lecturers on main page."""

    _main_page_content_type: str = LECTURERS_CONTENT_REF

    class Meta:
        verbose_name = _("Lecturers content item")
        verbose_name_plural = _("Lecturers content list")
        ordering = ["position_on_page", "created"]
