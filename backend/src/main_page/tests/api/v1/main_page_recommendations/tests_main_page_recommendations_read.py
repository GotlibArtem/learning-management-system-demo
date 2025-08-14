import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/main-page/recommendations/"


@pytest.fixture
def category(factory):
    return factory.category(
        name="Литература",
        slug="literatura",
    )


@pytest.fixture
def course(factory, category):
    return factory.course(
        name="Постапокалиптика в разрезе нового времени",
        slug="postapocaliptika-v-razreze",
        category=category,
        is_available_by_subscription=True,
        course_format="video",
        label="hit",
        lecturers_description="Описание лекторов",
        landing_url="https://awesome-course.test/",
    )


@pytest.fixture(autouse=True)
def course_version(factory, course):
    return factory.course_version(
        name="Новая версия постапокалиптики 2025",
        course=course,
        state="published",
    )


@pytest.fixture
def lecture_block(factory, lecture, block, course_plan):
    return factory.lecture_block(
        lecture=lecture,
        block=block,
        state="published",
        course_plans=[course_plan],
    )


@pytest.fixture(autouse=True)
def main_page_recommendation(factory, course, course_series):
    return factory.main_page_recommendation(course=course, course_series=course_series, position=0)


@pytest.fixture
def second_course(factory):
    recommendation = factory.main_page_recommendation(position=1)
    course = recommendation.course
    factory.course_version(course=course, state="published")
    return course


@pytest.fixture
def third_course(factory):
    recommendation = factory.main_page_recommendation(position=2)
    course = recommendation.course
    factory.course_version(course=course, state="published")
    return course


@pytest.fixture
def course_progress(factory, user, course):
    return factory.course_progress(user=user, course=course, completion_percent=77)


def test_some(second_course):
    pass


def test_read_list(as_user, course, course_progress):
    got = as_user.get(base_url)

    assert len(got) == 1

    got = got[0]
    assert got["name"] == "Постапокалиптика в разрезе нового времени"
    assert got["slug"] == "postapocaliptika-v-razreze"
    assert got["isAvailableBySubscription"] is True
    assert got["isFreeForAll"] is False
    assert got["isBookmarked"] is False
    assert got["courseFormat"] == "video"
    assert got["label"] == "hit"
    assert got["lecturesCount"] == 0
    assert got["isAvailable"] is False
    assert got["completionPercent"] == 77
    assert got["lecturersDescription"] == "Описание лекторов"
    assert got["durationInSeconds"] == 0
    assert got["landingUrl"] == "https://awesome-course.test/"
    assert set(got) == {
        "name",
        "slug",
        "isAvailableBySubscription",
        "isFreeForAll",
        "courseFormat",
        "label",
        "isAvailable",
        "discountAmount",
        "isBookmarked",
        "category",
        "previewLandscapeUrl",
        "previewLandscapeTimecode",
        "previewLandscapeDuration",
        "previewPortraitUrl",
        "previewPortraitTimecode",
        "previewPortraitDuration",
        "coverLandscape",
        "coverPortrait",
        "coverSquare",
        "lecturesCount",
        "lecturersInRecommendation",
        "lecturersDescription",
        "completionPercent",
        "durationInSeconds",
        "courseSeries",
        "description",
        "landingUrl",
        "redirectUrl",
        "shortDescription",
        "viewsCount",
        "hasSeries",
    }


def test_read_list_no_lecturers_from_other_courses(as_user, course, second_course, lecturer):
    second_course.lecturers.add(lecturer, through_defaults=dict(show_in_recommendation=True, position=1))

    got = as_user.get(base_url)

    assert not got[0]["lecturersInRecommendation"]


def test_read_list_lecturer_fields(as_user, course, lecturer):
    course.lecturers.add(lecturer, through_defaults=dict(show_in_recommendation=True, position=1))
    expected_lecturer_keys = {
        "id",
        "firstName",
        "lastName",
        "slug",
        "photo",
        "description",
        "shortDescription",
    }

    got = as_user.get(base_url)

    lecturer_data = got[0]["lecturersInRecommendation"][0]
    assert lecturer_data["slug"] == lecturer.slug
    assert lecturer_data["id"] == str(lecturer.id)
    assert lecturer_data["firstName"] == lecturer.first_name
    assert lecturer_data["lastName"] == lecturer.last_name
    assert lecturer_data["description"] == lecturer.description
    assert set(lecturer_data) == expected_lecturer_keys


def test_read_list_course_series_fields(as_user, course_series, course_version):
    course_series.setattr_and_save("state", "published")
    course_series.course_versions.set([course_version])

    got = as_user.get(base_url)[0]

    course_series_data = got["courseSeries"]
    assert course_series_data["slug"] == course_series.slug
    assert course_series_data["name"] == course_series.name
    assert course_series_data["courses"][0]["slug"] == course_version.course.slug
    assert set(course_series_data) == {
        "name",
        "slug",
        "courses",
    }
    assert set(course_series_data["courses"][0]) == {
        "name",
        "slug",
        "courseFormat",
        "label",
        "coverLandscape",
        "coverPortrait",
        "coverSquare",
        "landingUrl",
    }


@pytest.mark.usefixtures("lecture_block")
def test_read_list_with_lectures(as_user, course):
    course.setattr_and_save("denormalized_lectures_count", 15)

    got = as_user.get(base_url)

    assert len(got) == 1
    assert got[0]["lecturesCount"] == 15


def test_read_list_keep_recommendations_order(as_user, course, second_course, third_course):
    got = as_user.get(base_url)

    first, second, third = got
    assert first["slug"] == course.slug
    assert second["slug"] == second_course.slug
    assert third["slug"] == third_course.slug


def test_read_category(as_user, course, category):
    got = as_user.get(base_url)

    got = got[0]["category"]
    assert got["name"] == "Литература"
    assert got["slug"] == "literatura"
    assert set(got) == {"name", "slug"}


def test_courses_not_in_recommendation_are_hidden(as_user, main_page_recommendation):
    main_page_recommendation.delete()

    got = as_user.get(base_url)

    assert len(got) == 0
