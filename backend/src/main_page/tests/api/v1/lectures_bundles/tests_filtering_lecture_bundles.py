import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/main-page/lecture-bundles/"


@pytest.fixture
def first_lecture_bundle(factory):
    return factory.lecture_bundle_content(is_hidden=False, slug="its-just", position_on_page=1)


@pytest.fixture
def second_lecture_bundle(factory):
    return factory.lecture_bundle_content(is_hidden=False, slug="one-of", position_on_page=2)


@pytest.fixture
def third_lecture_bundle(factory):
    return factory.lecture_bundle_content(is_hidden=False, slug="those-days", position_on_page=3)


@pytest.mark.parametrize(("slugs", "expected_count"), [("its-just,those-days", 2), ("one-of", 1), ("made-up", 0)])
@pytest.mark.usefixtures("first_lecture_bundle", "second_lecture_bundle", "third_lecture_bundle")
def test_read_list(as_user, slugs, expected_count):
    url = f"{base_url}?slugs={slugs}"

    got = as_user.get(url)["results"]

    assert len(got) == expected_count
