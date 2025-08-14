import pytest


pytestmark = [pytest.mark.django_db]


base_url = "/api/demo/main-page/course-bundles/"


@pytest.fixture
def first_course_bundle(factory):
    return factory.course_bundle_content(is_hidden=False, slug="now-move-in", position_on_page=1)


@pytest.fixture
def second_course_bundle(factory):
    return factory.course_bundle_content(is_hidden=False, slug="now-move-out", position_on_page=2)


@pytest.fixture
def third_course_bundle(factory):
    return factory.course_bundle_content(is_hidden=False, slug="hands-up", position_on_page=3)


@pytest.mark.parametrize(("slugs", "expected_count"), [("now-move-in,hands-up", 2), ("now-move-out", 1), ("made-up", 0)])
@pytest.mark.usefixtures("first_course_bundle", "second_course_bundle", "third_course_bundle")
def test_read_list(as_user, slugs, expected_count):
    url = f"{base_url}?slugs={slugs}"

    got = as_user.get(url)["results"]

    assert len(got) == expected_count
