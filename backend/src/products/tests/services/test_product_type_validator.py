from contextlib import nullcontext as do_not_raise

import pytest

from products.services import ProductTypeValidatorException, product_type_validator


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def course_version_plan(course_version, course_plan):
    return {
        "course_version": str(course_version.pk),
        "course_plan": str(course_plan.pk),
    }


@pytest.mark.parametrize("product_type", ["subscription", "course-series"])
def test_only_course_type_can_contain_course_versions(course_version_plan, product_type):
    with pytest.raises(ProductTypeValidatorException):
        product_type_validator.validate(
            product_type=product_type,
            course_versions_plans=[course_version_plan],
            course_series=[],
        )


def test_course_type_has_to_contain_course_versions():
    with pytest.raises(ProductTypeValidatorException):
        product_type_validator.validate(
            product_type="course",
            course_versions_plans=[],
            course_series=[],
        )


@pytest.mark.parametrize("product_type", ["subscription", "course"])
def test_only_course_series_type_can_contain_course_series(course_series, product_type):
    with pytest.raises(ProductTypeValidatorException):
        product_type_validator.validate(
            product_type=product_type,
            course_versions_plans=[],
            course_series=[course_series],
        )


def test_course_series_type_has_to_contain_course_series():
    with pytest.raises(ProductTypeValidatorException):
        product_type_validator.validate(
            product_type="course-series",
            course_versions_plans=[],
            course_series=[],
        )


def test_course_plan_must_match_course_version(course_version_plan, factory, course_plan):
    course_plan.setattr_and_save("course_version", factory.course_version())

    with pytest.raises(ProductTypeValidatorException):
        product_type_validator.validate(
            product_type="course",
            course_versions_plans=[course_version_plan],
            course_series=[],
        )


def test_ignore_invalid_product_type(course_version_plan):
    with do_not_raise():
        product_type_validator.validate(
            product_type="invalid",
            course_versions_plans=[course_version_plan],
            course_series=[],
        )
