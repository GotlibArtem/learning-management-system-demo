import pytest


pytestmark = [pytest.mark.django_db]


base_url = "/api/demo/main-page/course-bundles/"


@pytest.fixture
def course(factory, course, user):
    factory.course_progress(user=user, course=course, completion_percent=90)
    return course


@pytest.fixture
def course_series(course_version, course_series):
    course_series.course_versions.add(course_version)
    return course_series


@pytest.fixture
def course_bundle(factory):
    return factory.course_bundle_content(
        is_hidden=False,
        badge_text="Лучшие курсы",
        badge_icon="lightning",
        badge_color="yellow",
    )


@pytest.fixture
def course_bundle_item(factory, course, course_version, course_bundle):
    return factory.course_bundle_item(bundle=course_bundle, course=course, position_in_course_bundle=1)


@pytest.fixture
def course_bundle_item_with_series(factory, course_series, course_bundle):
    return factory.course_bundle_item(bundle=course_bundle, course_series=course_series, position_in_course_bundle=2)


@pytest.fixture
def retrieve_url(course_bundle):
    return f"{base_url}{course_bundle.slug}/"


def test_read_list(as_user, course_bundle_item, course, course_bundle):
    got = as_user.get(base_url)["results"]

    assert len(got) == 1

    got = got[0]
    assert got["name"] == course_bundle.name
    assert got["slug"] == course_bundle.slug
    assert got["orientation"] == course_bundle.orientation
    assert got["badgeText"] == "Лучшие курсы"
    assert got["badgeIcon"] == "lightning"
    assert got["badgeColor"] == "yellow"
    assert set(got) == {
        "name",
        "slug",
        "orientation",
        "badgeText",
        "badgeIcon",
        "badgeColor",
        "items",
    }


def test_read_list_course_field(as_user, course_bundle_item, course, course_bundle):
    got = as_user.get(base_url)["results"][0]["items"]

    assert len(got) == 1

    got = got[0]
    assert got["name"] == course.name
    assert got["slug"] == course.slug
    assert got["completionPercent"] == 90
    assert set(got) == {
        "name",
        "slug",
        "coverLandscape",
        "coverPortrait",
        "coverSquare",
        "previewLandscapeUrl",
        "previewLandscapeTimecode",
        "previewLandscapeDuration",
        "previewPortraitUrl",
        "previewPortraitTimecode",
        "previewPortraitDuration",
        "isAvailableBySubscription",
        "isFreeForAll",
        "courseFormat",
        "label",
        "isAvailable",
        "discountAmount",
        "isBookmarked",
        "lecturesCount",
        "category",
        "completionPercent",
        "durationInSeconds",
        "description",
        "shortDescription",
        "landingUrl",
        "redirectUrl",
        "viewsCount",
        "hasSeries",
    }


def test_read_list_course_series_field(as_user, course_bundle_item_with_series, course_series, course_bundle):
    got = as_user.get(base_url)["results"][0]["items"]

    assert len(got) == 1

    got = got[0]
    assert got["name"] == course_series.name
    assert got["slug"] == course_series.slug
    assert got["completionPercent"] == 90
    assert got["coursesCount"] == 1
    assert len(got["courses"]) == 1
    assert set(got) == {
        "name",
        "slug",
        "coursesCount",
        "isAvailable",
        "isBookmarked",
        "courses",
        "completionPercent",
        "landingUrl",
        "isAvailableBySubscription",
        "isFreeForAll",
    }
    assert set(got["courses"][0]) == {
        "name",
        "slug",
        "label",
        "courseFormat",
        "coverLandscape",
        "coverPortrait",
        "coverSquare",
        "landingUrl",
    }


def test_read_single(as_user, retrieve_url, course_bundle):
    got = as_user.get(retrieve_url)

    assert got["name"] == course_bundle.name
    assert got["slug"] == course_bundle.slug
    assert got["orientation"] == course_bundle.orientation
    assert got["badgeText"] == "Лучшие курсы"
    assert got["badgeIcon"] == "lightning"
    assert got["badgeColor"] == "yellow"
    assert set(got) == {
        "name",
        "slug",
        "orientation",
        "badgeText",
        "badgeIcon",
        "badgeColor",
        "items",
    }


def test_read_respects_items_order_in_bundle_1(as_user, retrieve_url, course_bundle_item, course_bundle_item_with_series):
    course_bundle_item.setattr_and_save("position_in_course_bundle", 1)
    course_bundle_item_with_series.setattr_and_save("position_in_course_bundle", 2)

    got = as_user.get(retrieve_url)

    first, second = got["items"]
    assert first["slug"] == course_bundle_item.course.slug
    assert second["slug"] == course_bundle_item_with_series.course_series.slug


def test_read_respects_items_order_in_bundle_2(as_user, retrieve_url, course_bundle_item, course_bundle_item_with_series):
    course_bundle_item.setattr_and_save("position_in_course_bundle", 2)
    course_bundle_item_with_series.setattr_and_save("position_in_course_bundle", 1)

    got = as_user.get(retrieve_url)

    first, second = got["items"]
    assert first["slug"] == course_bundle_item_with_series.course_series.slug
    assert second["slug"] == course_bundle_item.course.slug


def test_show_only_published_courses_items(as_user, retrieve_url, course_bundle_item, course_version):
    course_version.setattr_and_save("state", "archived")

    got = as_user.get(retrieve_url)["items"]

    assert len(got) == 0


def test_show_only_published_series_items(as_user, retrieve_url, course_bundle_item_with_series, course_series):
    course_series.setattr_and_save("state", "closed")

    got = as_user.get(retrieve_url)["items"]

    assert len(got) == 0
