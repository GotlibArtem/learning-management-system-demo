import pytest


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def create_content(factory):
    def _create_content(count):
        factory.cycle(count).lecturer()
        factory.cycle(count).category()

        factory.cycle(count).lecturers_content(is_hidden=False)
        factory.cycle(count).categories_content(is_hidden=False)

        courses = factory.cycle(count).course()
        lectures = factory.cycle(count).lecture()
        course_series = factory.cycle(count).course_series()

        lecture_bundles = factory.cycle(count).lecture_bundle_content(is_hidden=False)
        for bundle in lecture_bundles:
            for lecture in lectures:
                factory.lecture_bundle_item(bundle=bundle, lecture=lecture)

        course_bundles = factory.cycle(count).course_bundle_content(is_hidden=False)
        for bundle in course_bundles:
            for course in courses:
                factory.course_bundle_item(bundle=bundle, course=course)
            for series in course_series:
                factory.course_bundle_item(bundle=bundle, course_series=series)

    return _create_content


@pytest.mark.parametrize("count", [2, 4])
def test_content_list_read_no_nplus_one_queries(as_user, django_assert_max_num_queries, create_content, count):
    create_content(count)

    with django_assert_max_num_queries(10):
        assert as_user.get("/api/demo/main-page/content/"), "Empty setup error!"
