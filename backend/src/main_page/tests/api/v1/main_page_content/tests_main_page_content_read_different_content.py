import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/main-page/content/"


@pytest.fixture
def lecturers_content(factory):
    return factory.lecturers_content(
        name="Наши мордашки",
        is_hidden=False,
        position_on_page=1,
    )


@pytest.fixture
def categories_content(factory):
    return factory.categories_content(
        name="Наши направляшки",
        is_hidden=False,
        position_on_page=2,
    )


@pytest.fixture
def lecture_bundle_content(factory):
    return factory.lecture_bundle_content(
        name="Наши уроки",
        is_hidden=False,
        position_on_page=3,
    )


@pytest.fixture
def course_bundle_content(factory):
    return factory.course_bundle_content(
        name="Наши курсы",
        is_hidden=False,
        position_on_page=4,
    )


def test_read_list(as_user, lecturers_content, categories_content, lecture_bundle_content, course_bundle_content):
    got_all = as_user.get(base_url)["results"]

    assert len(got_all) == 4

    got = got_all[0]
    assert got["id"] == str(lecturers_content.id)
    assert got["mainPageContentType"] == "lecturers-content"
    assert got["content"]["name"] == "Наши мордашки"
    assert set(got["content"]) == {"name", "lecturers"}

    got = got_all[1]
    assert got["id"] == str(categories_content.id)
    assert got["mainPageContentType"] == "categories-content"
    assert got["content"]["name"] == "Наши направляшки"
    assert set(got["content"]) == {"name", "categories"}

    got = got_all[2]
    assert got["id"] == str(lecture_bundle_content.id)
    assert got["mainPageContentType"] == "lecture-bundle-content"
    assert got["content"]["name"] == "Наши уроки"
    assert set(got["content"]) == {"slug", "name", "badgeText", "badgeIcon", "badgeColor"}

    got = got_all[3]
    assert got["id"] == str(course_bundle_content.id)
    assert got["mainPageContentType"] == "course-bundle-content"
    assert got["content"]["name"] == "Наши курсы"
    assert set(got["content"]) == {"slug", "name", "orientation", "badgeText", "badgeIcon", "badgeColor"}


def test_ordering_according_to_position_field_1(as_user, lecturers_content, categories_content, factory):
    new_content = factory.lecturers_content(position_on_page=0, is_hidden=False)

    got_all = as_user.get(base_url)["results"]

    assert len(got_all) == 3

    assert got_all[0]["id"] == str(new_content.id)
    assert got_all[1]["id"] == str(lecturers_content.id)
    assert got_all[2]["id"] == str(categories_content.id)


def test_ordering_according_to_position_field_2(as_user, lecturers_content, categories_content, factory):
    new_content = factory.lecturers_content(position_on_page=10, is_hidden=False)

    got_all = as_user.get(base_url)["results"]

    assert len(got_all) == 3

    assert got_all[0]["id"] == str(lecturers_content.id)
    assert got_all[1]["id"] == str(categories_content.id)
    assert got_all[2]["id"] == str(new_content.id)


def test_hidden_content(as_user, lecturers_content, categories_content):
    lecturers_content.setattr_and_save("is_hidden", True)

    got = as_user.get(base_url)["results"]

    assert len(got) == 1
    assert got[0]["id"] == str(categories_content.id)
