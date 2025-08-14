from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel


class MainPageRecommendation(TimestampedModel):
    course = models.ForeignKey(
        "courses.Course",
        verbose_name=_("Course"),
        on_delete=models.PROTECT,
    )
    position = models.PositiveSmallIntegerField(verbose_name=_("Position"), default=1, db_index=True)

    class Meta:
        verbose_name = _("Main page recommendation")
        verbose_name_plural = _("Main page recommendations")
        ordering = ["position"]
        default_related_name = "main_page_recommendations"

    def __str__(self) -> str:
        return f"{self.course.name} main page recommendation"
