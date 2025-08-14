import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/main-page/content/"


@pytest.fixture
def category_art(factory):
    return factory.category(name="Искусство", slug="art")


@pytest.fixture
def category_psychology(factory):
    return factory.category(name="Психология", slug="psychology")


@pytest.fixture
def course_bundle_with_art(factory, category_art):
    return factory.course_bundle_content(
        name="Искусство",
        is_hidden=False,
        position_on_page=5,
        personalization_categories=[category_art],
    )


@pytest.fixture
def course_bundle_with_psychology(factory, category_psychology):
    return factory.course_bundle_content(
        name="Психология",
        is_hidden=False,
        position_on_page=2,
        personalization_categories=[category_psychology],
    )


@pytest.fixture
def course_bundle_common(factory):
    return factory.course_bundle_content(
        name="Общая подборка",
        is_hidden=False,
        position_on_page=1,
    )


def test_personalized_content_moves_up_single_interest(
    as_user,
    user,
    course_bundle_with_art,
    course_bundle_with_psychology,
    course_bundle_common,
    category_art,
):
    user.interests.add(category_art)

    got = as_user.get(base_url)["results"]

    assert len(got) == 3
    assert got[0]["id"] == str(course_bundle_with_art.id)
    assert got[1]["id"] == str(course_bundle_common.id)
    assert got[2]["id"] == str(course_bundle_with_psychology.id)


def test_personalized_content_moves_up_multiple_interests(
    as_user,
    user,
    course_bundle_with_art,
    course_bundle_with_psychology,
    course_bundle_common,
    category_art,
    category_psychology,
):
    user.interests.add(category_art, category_psychology)

    got = as_user.get(base_url)["results"]

    assert len(got) == 3
    assert got[0]["id"] == str(course_bundle_with_psychology.id)
    assert got[1]["id"] == str(course_bundle_with_art.id)
    assert got[2]["id"] == str(course_bundle_common.id)


def test_no_personalization_if_no_interests(as_user, course_bundle_with_art, course_bundle_with_psychology, course_bundle_common):
    got = as_user.get(base_url)["results"]

    assert len(got) == 3
    assert got[0]["id"] == str(course_bundle_common.id)
    assert got[1]["id"] == str(course_bundle_with_psychology.id)
    assert got[2]["id"] == str(course_bundle_with_art.id)


def test_no_personalization_if_user_selected_all_interests(
    as_user,
    user,
    course_bundle_with_art,
    course_bundle_with_psychology,
    course_bundle_common,
    category_art,
    category_psychology,
):
    user.interests.add(category_art, category_psychology)
    user.all_interests = True
    user.save()

    got = as_user.get(base_url)["results"]

    assert len(got) == 3
    assert got[0]["id"] == str(course_bundle_common.id)
    assert got[1]["id"] == str(course_bundle_with_psychology.id)
    assert got[2]["id"] == str(course_bundle_with_art.id)
