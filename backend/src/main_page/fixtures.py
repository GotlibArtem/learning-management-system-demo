from typing import TYPE_CHECKING

import pytest

from main_page.models import CategoriesContent, CourseBundleContent, LectureBundleContent, LecturersContent


if TYPE_CHECKING:
    from app.testing.factory import FixtureFactory


@pytest.fixture
def lecturers_content(factory: "FixtureFactory") -> LecturersContent:
    return factory.lecturers_content()


@pytest.fixture
def categories_content(factory: "FixtureFactory") -> CategoriesContent:
    return factory.categories_content()


@pytest.fixture
def course_bundle_content(factory: "FixtureFactory") -> CourseBundleContent:
    return factory.course_bundle_content()


@pytest.fixture
def lecture_bundle_content(factory: "FixtureFactory") -> LectureBundleContent:
    return factory.lecture_bundle_content()
