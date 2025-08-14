from django.utils.translation import gettext_lazy as _

from app.models import models
from main_page.models.main_page_content import COURSE_BUNDLE_CONTENT_REF, MainPageContent
from main_page.models.mixins import MainPageContentParentLinkMixin


class CourseBundleContent(MainPageContentParentLinkMixin, MainPageContent):  # type: ignore
    _main_page_content_type: str = COURSE_BUNDLE_CONTENT_REF

    orientation = models.CharField(
        verbose_name=_("Orientation"),
        max_length=20,
        choices=[
            ("portrait", _("Portrait")),
            ("landscape", _("Landscape")),
            ("landscape-large", _("Landscape large")),
        ],
    )
    slug = models.SlugField(max_length=255, unique=True)

    personalization_categories = models.ManyToManyField(
        "courses.Category",
        blank=True,
        verbose_name=_("Personalization categories"),
        related_name="course_bundles",
        help_text=_("Select the categories that will personalize this bundle for users with matching interests."),
    )

    class Meta:
        verbose_name = _("Course bundle content item")
        verbose_name_plural = _("Course bundle content list")
        ordering = ["position_on_page", "created"]
