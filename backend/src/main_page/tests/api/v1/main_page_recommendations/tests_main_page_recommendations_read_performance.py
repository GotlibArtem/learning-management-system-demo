import pytest


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def create_recommendations(factory):
    def _create_recommendations(count):
        course_versions = factory.cycle(count).course_version(state="published")
        for course_version in course_versions:
            series = factory.course_series(state="published")
            series.course_versions.add(course_version)
            factory.main_page_recommendation(course=course_version.course)
            lecture = factory.lecture(courses=[course_version.course])
            block = factory.block(course_version=course_version)
            factory.course_version_telegram(course_version=course_version)
            factory.lecture_block(
                lecture=lecture,
                block=block,
                state="published",
            )
            lecturer = factory.lecturer()
            course_version.course.lecturers.add(lecturer)

    return _create_recommendations


@pytest.mark.parametrize("count", [2, 4])
def test_recommendations_list_read_no_nplus_one_queries(as_user, django_assert_max_num_queries, create_recommendations, count):
    create_recommendations(count)

    with django_assert_max_num_queries(22):
        assert as_user.get("/api/demo/main-page/recommendations/"), "Empty setup error!"
