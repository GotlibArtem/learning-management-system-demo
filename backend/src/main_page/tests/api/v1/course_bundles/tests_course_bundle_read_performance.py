import pytest


pytestmark = [pytest.mark.django_db]


@pytest.fixture
def create_course_bundles(factory, user):
    def _create_course_bundles(count):
        bundles = factory.cycle(count).course_bundle_content(is_hidden=False)
        for bundle in bundles:
            courses = factory.cycle(count).course()
            course_series = factory.cycle(count).course_series()
            for course in courses:
                factory.course_bundle_item(bundle=bundle, course=course, course_series=None)
                factory.course_progress(user=user, course=course)
            for series in course_series:
                factory.course_bundle_item(bundle=bundle, course_series=series, course=None)
                courses = factory.cycle(count).course()
                for course in courses:
                    factory.course_version(
                        course=course,
                        state="published",
                        course_series=series,
                    )
                    factory.course_progress(user=user, course=course)

    return _create_course_bundles


@pytest.mark.parametrize("count", [2, 4])
def test_course_bundles_list_no_nplus_one_queries(as_user, django_assert_max_num_queries, create_course_bundles, count):
    create_course_bundles(count)

    with django_assert_max_num_queries(22):
        as_user.get("/api/demo/main-page/course-bundles/")
