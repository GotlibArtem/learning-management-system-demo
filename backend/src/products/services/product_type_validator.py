from collections.abc import Callable, Collection

from django.utils.translation import gettext as _

from app.exceptions import AppServiceException


Validator = Callable[[Collection[dict], Collection[dict]], None]


class ProductTypeValidatorException(AppServiceException):
    """Use for any product type validation error"""


def validate_course_type(
    course_versions_plans: Collection[dict],
    course_series: Collection[dict],
) -> None:
    if len(course_versions_plans) == 0:
        raise ProductTypeValidatorException(_("Product of course type has to contain course versions"))

    if len(course_series) != 0:
        raise ProductTypeValidatorException(_("Product of course type can't contain course series"))

    for course_version_plan in course_versions_plans:
        course_plan = CoursePlan.objects.get(id=course_version_plan["course_plan"])
        if str(course_plan.course_version.pk) != course_version_plan["course_version"]:
            raise ProductTypeValidatorException(_(f"Course plan {course_plan} doesn't match related course version"))


def validate_subscription_type(
    course_versions_plans: Collection[dict],
    course_series: Collection[dict],
) -> None:
    if len(course_versions_plans) != 0:
        raise ProductTypeValidatorException(_("Product of subscription type can't contain course versions"))

    if len(course_series) != 0:
        raise ProductTypeValidatorException(_("Product of subscription type can't contain course series"))


def validate_course_series_type(
    course_versions_plans: Collection[dict],
    course_series: Collection[dict],
) -> None:
    if len(course_series) == 0:
        raise ProductTypeValidatorException(_("Product of course series type has to contain course series"))

    if len(course_versions_plans) != 0:
        raise ProductTypeValidatorException(_("Product of course series type can't contain course versions"))


def validate(
    product_type: str,
    course_series: Collection[dict],
    course_versions_plans: Collection[dict],
) -> None:
    try:
        validators: dict[str, Validator] = {
            "subscription": validate_subscription_type,
            "course-series": validate_course_series_type,
            "course": validate_course_type,
        }
        validators[product_type](course_versions_plans, course_series)
    except KeyError:
        return None
