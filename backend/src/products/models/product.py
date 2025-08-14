from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel


class Product(TimestampedModel):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
    )
    product_type = models.CharField(
        verbose_name=_("Type"),
        choices=[
            ("course", _("Course")),
            ("course-series", _("Course series")),
            ("subscription", _("Subscription")),
        ],
        db_index=True,
    )
    shop_id = models.CharField(
        verbose_name=_("Shop ID"),
        max_length=128,
        blank=True,
        db_index=True,
    )
    apple_product_id = models.CharField(
        verbose_name=_("Apple product ID"),
        max_length=128,
        blank=True,
        db_index=True,
    )
    lifetime = models.PositiveIntegerField(
        verbose_name=_("Lifetime (in days)"),
        null=True,
        blank=True,
        help_text=_("How many days access is granted after purchase."),
    )

    course_series = models.ManyToManyField(
        "courses.CourseSeries",
        verbose_name=_("Course series"),
        related_name="products",
        blank=True,
    )
    course_versions_plans = models.ManyToManyField(
        "courses.CourseVersion",
        verbose_name=_("Course versions plans"),
        related_name="products",
        blank=True,
        through="products.CourseVersionPlanProduct",
    )

    redirect_url = models.URLField(
        verbose_name=_("Redirect URL"),
        max_length=255,
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["shop_id"],
                name="unique_or_empty_product_shop_id",
                condition=~Q(shop_id=""),
            ),
        ]
        indexes = [
            models.Index(fields=["product_type", "-created"], name="product_producttypecreated_idx"),
        ]

    def __str__(self) -> str:
        return self.name
