from django.db import models

from app.models import TimestampedModel


class CourseVersionPlanProduct(TimestampedModel):
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    course_version = models.ForeignKey("courses.CourseVersion", on_delete=models.CASCADE)
    course_plan = models.ForeignKey("courses.CoursePlan", on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=["product", "course_version", "course_plan"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["product", "course_version"], name="unique_product_course_version"),
        ]
        ordering = ["created"]
        default_related_name = "course_version_plans"
