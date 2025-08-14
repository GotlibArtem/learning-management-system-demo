import pytest
from django.db.utils import IntegrityError

from main_page.models import CategoriesContent, CourseBundleContent, LectureBundleContent, LecturersContent, MainPageContent
from main_page.models.main_page_content import CATEGORIES_CONTENT_REF, COURSE_BUNDLE_CONTENT_REF, LECTURE_BUNDLE_CONTENT_REF, LECTURERS_CONTENT_REF


pytestmark = [
    pytest.mark.django_db,
]


def test_lecturers_has_correct_autotype():
    lecturers_content = LecturersContent.objects.create(
        name="Целая. Карусель. Лекторов.",
        position_on_page=100,
        is_hidden=False,
    )

    lecturers_content.refresh_from_db()
    assert lecturers_content.main_page_content_type == LECTURERS_CONTENT_REF


def test_lecturers_has_correct_fields_in_fixture(lecturers_content):
    assert lecturers_content.main_page_content_type == LECTURERS_CONTENT_REF


def test_categories_has_correct_autotype():
    categories_content = CategoriesContent.objects.create(
        name="Целая. Карусель. Направлений.",
        position_on_page=100,
        is_hidden=False,
    )

    categories_content.refresh_from_db()
    assert categories_content.main_page_content_type == CATEGORIES_CONTENT_REF


def test_categories_has_correct_fields_in_fixture(categories_content):
    assert categories_content.main_page_content_type == CATEGORIES_CONTENT_REF


def test_course_bundle_has_correct_autotype():
    course_bundle_content = CourseBundleContent.objects.create(
        name="Целая. Карусель. Курсов.",
        position_on_page=100,
        is_hidden=False,
    )

    course_bundle_content.refresh_from_db()
    assert course_bundle_content.main_page_content_type == COURSE_BUNDLE_CONTENT_REF


def test_course_bundle_has_correct_fields_in_fixture(course_bundle_content):
    assert course_bundle_content.main_page_content_type == COURSE_BUNDLE_CONTENT_REF


def test_lecture_bundle_has_correct_autotype():
    lecture_bundle_content = LectureBundleContent.objects.create(
        name="Целая. Карусель. Уроков.",
        position_on_page=100,
        is_hidden=False,
    )

    lecture_bundle_content.refresh_from_db()
    assert lecture_bundle_content.main_page_content_type == LECTURE_BUNDLE_CONTENT_REF


def test_lecture_bundle_has_correct_fields_in_fixture(lecture_bundle_content):
    assert lecture_bundle_content.main_page_content_type == LECTURE_BUNDLE_CONTENT_REF


@pytest.mark.parametrize(
    "content_type_fixture",
    ["lecturers_content", "categories_content", "course_bundle_content", "lecture_bundle_content"],
)
def test_subclass_instance_method_loads_correct_content_by_type(request, content_type_fixture):
    expected_content = request.getfixturevalue(content_type_fixture)
    main_page_content = MainPageContent.objects.get(id=expected_content.main_page_content_id)

    assert main_page_content.subclass_instance == expected_content


@pytest.mark.parametrize("main_page_content_type", ["some-invalid-type", ""])
def test_raise_if_text_content_type_has_no_representation_as_a_field(lecturers_content, main_page_content_type):
    lecturers_content.setattr_and_save("main_page_content_type", main_page_content_type)

    main_page_content = MainPageContent.objects.get(id=lecturers_content.main_page_content_id)

    with pytest.raises(ValueError, match="Cannot define back link to content model."):
        assert main_page_content.subclass_instance


@pytest.mark.parametrize("main_page_content_type", ["id", "name"])
def test_raise_if_content_type_is_not_a_valid_content_model(lecturers_content, main_page_content_type):
    lecturers_content.setattr_and_save("main_page_content_type", main_page_content_type)

    main_page_content = MainPageContent.objects.get(id=lecturers_content.main_page_content_id)

    with pytest.raises(ValueError, match="Content model is not a subclass of MainPageContent"):
        assert main_page_content.subclass_instance


@pytest.mark.parametrize("model", [LectureBundleContent, CourseBundleContent])
def test_allow_all_badge_fields_empty(model):
    model.objects.create(
        name="Целая. Карусель.",
        badge_text="",
        badge_icon="",
        badge_color="",
    )

    assert MainPageContent.objects.count() == 1


@pytest.mark.parametrize("model", [LectureBundleContent, CourseBundleContent])
def test_allow_all_badge_fields_filled(model):
    model.objects.create(
        name="Целая. Карусель.",
        badge_text="New",
        badge_icon="star",
        badge_color="yellow",
    )

    assert MainPageContent.objects.count() == 1


@pytest.mark.parametrize(
    ("text", "icon", "color"),
    [
        ("New", "", ""),
        ("", "star", ""),
        ("", "", "yellow"),
        ("New", "star", ""),
        ("New", "", "yellow"),
        ("", "star", "yellow"),
    ],
)
@pytest.mark.parametrize("model", [LectureBundleContent, CourseBundleContent])
def test_fail_if_badge_fields_partially_filled(model, text, icon, color):
    with pytest.raises(IntegrityError):
        model.objects.create(
            name="Целая. Карусель.",
            badge_text=text,
            badge_icon=icon,
            badge_color=color,
        )
