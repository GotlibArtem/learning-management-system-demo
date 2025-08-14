from typing import Self

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel, models
from main_page.types import MainPageContentType
from users.models import User


LECTURERS_CONTENT_REF = "lecturerscontent"
CATEGORIES_CONTENT_REF = "categoriescontent"
LECTURE_BUNDLE_CONTENT_REF = "lecturebundlecontent"
COURSE_BUNDLE_CONTENT_REF = "coursebundlecontent"


class MainPageContentQuerySet(models.QuerySet):
    def for_viewset(self) -> Self:
        return self.active().select_related(
            LECTURERS_CONTENT_REF,
            CATEGORIES_CONTENT_REF,
            LECTURE_BUNDLE_CONTENT_REF,
            COURSE_BUNDLE_CONTENT_REF,
        )

    def active(self) -> Self:
        return self.filter(is_hidden=False)

    def with_personalization(self, user: User) -> Self:
        from main_page.models import CourseBundleContent, LectureBundleContent

        user_interest_ids = user.interests.values_list("id", flat=True)

        return self.annotate(
            is_personalized=(
                models.Exists(
                    CourseBundleContent.objects.filter(
                        personalization_categories__in=user_interest_ids,
                        pk=models.OuterRef("pk"),
                    ),
                )
                | models.Exists(
                    LectureBundleContent.objects.filter(
                        personalization_categories__in=user_interest_ids,
                        pk=models.OuterRef("pk"),
                    ),
                )
            ),
        )


MainPageContentManager = models.Manager.from_queryset(MainPageContentQuerySet)


class MainPageContent(TimestampedModel):
    """
    Mother table linked to some piece of educational content.
    Only one content type (e.g. CourseBundle) is allowed per one MainPageContent.

    Caution! That`s a concrete model not an abstract one.
    Check docs https://docs.djangoproject.com/en/4.0/topics/db/models/#multi-table-inheritance
    """

    objects = MainPageContentManager()

    main_page_content_type = models.CharField(
        choices=[
            (LECTURERS_CONTENT_REF, _("Lecturers")),
            (CATEGORIES_CONTENT_REF, _("Categories")),
            (LECTURE_BUNDLE_CONTENT_REF, _("Lectures bundle")),
            (COURSE_BUNDLE_CONTENT_REF, _("Courses bundle")),
        ],
        max_length=50,
        verbose_name=_("Main page content type"),
    )

    name = models.CharField(_("Name"), max_length=255)
    position_on_page = models.PositiveSmallIntegerField(_("Position on the main page"), default=1)
    is_hidden = models.BooleanField(_("Is hidden"), default=True, db_index=True)

    badge_color = models.CharField(
        verbose_name=_("Badge color"),
        max_length=20,
        choices=[
            ("yellow", _("yellow")),
            ("peach", _("peach")),
            ("light-green", _("light-green")),
            ("lilac", _("lilac")),
            ("pink", _("pink")),
        ],
        blank=True,
    )
    badge_icon = models.CharField(
        verbose_name=_("Badge icon"),
        max_length=20,
        choices=[
            ("lightning", _("lightning")),
            ("flame", _("flame")),
            ("heart", _("heart")),
            ("star", _("star")),
            ("note", _("note")),
        ],
        blank=True,
    )
    badge_text = models.CharField(
        verbose_name=_("Badge text"),
        max_length=20,
        blank=True,
    )

    class Meta:
        ordering = ["position_on_page", "created"]
        verbose_name = _("Main page content item")
        verbose_name_plural = _("Main page content items")
        indexes = [
            models.Index(fields=["position_on_page", "created"]),
            models.Index(fields=["position_on_page"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(badge_text="", badge_icon="", badge_color="") | (~models.Q(badge_text="") & ~models.Q(badge_icon="") & ~models.Q(badge_color=""))
                ),
                name="badge_fields_must_be_filled_together",
            ),
        ]

    @cached_property
    def subclass_instance(self) -> MainPageContentType:
        """Get linked instance in optimized way by its text content type."""

        if not self.main_page_content_type or not hasattr(self, self.main_page_content_type):
            raise ValueError("Cannot define back link to content model.")

        instance = getattr(self, self.main_page_content_type)

        if not isinstance(instance, MainPageContent):
            raise ValueError("Content model is not a subclass of MainPageContent")  # noqa: TRY004

        return instance
