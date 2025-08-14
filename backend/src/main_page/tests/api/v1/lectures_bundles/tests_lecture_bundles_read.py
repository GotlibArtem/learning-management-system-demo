import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/main-page/lecture-bundles/"


@pytest.fixture
def course_version(factory, course):
    return factory.course_version(
        name="Новая версия постапокалиптики 2025",
        course=course,
        state="published",
    )


@pytest.fixture
def lecture_block(factory, lecture, block):
    return factory.lecture_block(
        lecture=lecture,
        block=block,
        state="published",
    )


@pytest.fixture
def lecture_bundle(factory):
    return factory.lecture_bundle_content(
        is_hidden=False,
        badge_text="Лучшие уроки",
        badge_icon="flame",
        badge_color="lilac",
    )


@pytest.fixture
def lecture_bundle_item(factory, lecture_block, lecture_bundle):
    return factory.lecture_bundle_item(bundle=lecture_bundle, lecture=lecture_block.lecture)


@pytest.fixture
def retrieve_url(lecture_bundle):
    return f"{base_url}{lecture_bundle.slug}/"


def test_read_list(as_user, lecture_bundle_item, lecture, lecture_bundle):
    got = as_user.get(base_url)["results"]

    assert len(got) == 1

    got = got[0]
    assert got["name"] == lecture_bundle.name
    assert got["slug"] == lecture_bundle.slug
    assert got["badgeText"] == "Лучшие уроки"
    assert got["badgeIcon"] == "flame"
    assert got["badgeColor"] == "lilac"
    assert set(got) == {
        "name",
        "slug",
        "badgeText",
        "badgeIcon",
        "badgeColor",
        "lectures",
    }


def test_read_list_lectures_field(as_user, lecture_bundle_item, lecture, lecture_bundle):
    got = as_user.get(base_url)["results"][0]["lectures"]

    assert len(got) == 1

    got = got[0]
    assert got["name"] == lecture.name
    assert got["slug"] == lecture.slug
    assert set(got) == {
        "block",
        "name",
        "slug",
        "contentUrl",
        "scheduledAt",
        "isAvailable",
        "durationInSeconds",
        "course",
        "progress",
        "description",
        "coverLandscape",
    }


@pytest.mark.usefixtures("lecture_bundle", "lecture_bundle_item")
def test_read_list_block(as_user, retrieve_url, block):
    got_block = as_user.get(retrieve_url)["lectures"][0]["block"]

    assert got_block["name"] == block.name
    assert got_block["slug"] == block.slug
    assert set(got_block) == {"name", "slug"}


def test_read_single(as_user, retrieve_url, lecture_bundle):
    got = as_user.get(retrieve_url)

    assert got["name"] == lecture_bundle.name
    assert got["slug"] == lecture_bundle.slug
    assert got["badgeText"] == "Лучшие уроки"
    assert got["badgeIcon"] == "flame"
    assert got["badgeColor"] == "lilac"
    assert set(got) == {
        "name",
        "slug",
        "badgeText",
        "badgeIcon",
        "badgeColor",
        "lectures",
    }


def test_read_respects_lectures_order_in_bundle(factory, as_user, retrieve_url, lecture_bundle, course_version):
    second_item = factory.lecture_bundle_item(bundle=lecture_bundle, position_in_lecture_bundle=2, lecture__courses=[course_version.course])
    first_item = factory.lecture_bundle_item(bundle=lecture_bundle, position_in_lecture_bundle=1, lecture__courses=[course_version.course])

    got = as_user.get(retrieve_url)

    first, second = got["lectures"]
    assert first["slug"] == first_item.lecture.slug
    assert second["slug"] == second_item.lecture.slug


def test_show_lectures_only_from_published_courses(as_user, retrieve_url, lecture_bundle_item):
    lecture_bundle_item.lecture.courses.first().course_versions.update(state="archived")

    got = as_user.get(retrieve_url)["lectures"]

    assert len(got) == 0
