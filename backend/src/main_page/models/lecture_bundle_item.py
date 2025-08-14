from typing import Self

from django.apps import apps
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel, models
from users.models import User


class LectureBundleItemQuerySet(models.QuerySet):
    def for_viewset(self, user: User) -> Self:
        Lecture = apps.get_model("courses", "Lecture")
        lectures_prefetch = Prefetch("lecture", queryset=Lecture.objects.personalized(user).with_courses(user).prefetch_published_lecture_blocks())
        return self.prefetch_related(lectures_prefetch).filter_with_published_courses().order_by("position_in_lecture_bundle")

    def filter_with_published_courses(self) -> Self:
        return self.filter(lecture__courses__course_versions__state="published").distinct()


class LectureBundleItem(TimestampedModel):
    objects = models.Manager.from_queryset(LectureBundleItemQuerySet)()

    bundle = models.ForeignKey("main_page.LectureBundleContent", on_delete=models.CASCADE, verbose_name=_("Lecture bundle"), related_name="items")
    lecture = models.ForeignKey("courses.Lecture", verbose_name=_("Lecture"), on_delete=models.PROTECT, related_name="lecture_bundle_items")

    position_in_lecture_bundle = models.PositiveSmallIntegerField(verbose_name=_("Position in lectures bundle"), default=1, db_index=True)

    class Meta:
        verbose_name = _("Lecture bundle item")
        verbose_name_plural = _("Lecture bundle items")
        ordering = ["position_in_lecture_bundle"]
        constraints = [
            models.UniqueConstraint(fields=["bundle", "lecture"], name="unique_lecture_per_bundle"),
        ]
