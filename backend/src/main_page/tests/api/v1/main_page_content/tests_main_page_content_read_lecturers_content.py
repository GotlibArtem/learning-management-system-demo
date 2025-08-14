import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/main-page/content/"


@pytest.fixture(autouse=True)
def lecturers_content(factory):
    return factory.lecturers_content(
        name="Наши мордашки",
        is_hidden=False,
    )


def test_read(as_user, lecturers_content):
    got = as_user.get(base_url)["results"]

    assert len(got) == 1

    got = got[0]
    assert got["id"] == str(lecturers_content.id)
    assert got["mainPageContentType"] == "lecturers-content"


def test_content(as_user, lecturers_content):
    got = as_user.get(base_url)["results"]

    content = got[0]["content"]
    assert content["name"] == "Наши мордашки"
    assert "lecturers" in content


def test_read_lecturers_list(as_user, factory):
    factory.cycle(3).lecturer()

    got = as_user.get(base_url)["results"]

    lecturers = got[0]["content"]["lecturers"]
    assert len(lecturers) == 3


def test_hide_not_visible_lecturers(as_user, factory):
    factory.cycle(2).lecturer(show_in_main_page=False)

    got = as_user.get(base_url)["results"]

    lecturers = got[0]["content"]["lecturers"]
    assert len(lecturers) == 0


def test_read_list_lecturer_fields(as_user, lecturer):
    expected_lecturer_keys = {
        "id",
        "firstName",
        "lastName",
        "slug",
        "photo",
        "description",
        "shortDescription",
    }

    got = as_user.get(base_url)["results"]

    lecturer_data = got[0]["content"]["lecturers"][0]
    assert lecturer_data["slug"] == lecturer.slug
    assert lecturer_data["id"] == str(lecturer.id)
    assert lecturer_data["firstName"] == lecturer.first_name
    assert lecturer_data["lastName"] == lecturer.last_name
    assert lecturer_data["description"] == lecturer.description
    assert lecturer_data["shortDescription"] == lecturer.short_description
    assert set(lecturer_data) == expected_lecturer_keys


def test_limit_lecturers_number(factory, as_user, settings):
    factory.cycle(12).lecturer()
    settings.MAX_LECTURERS_ON_MAIN_PAGE = 5

    got = as_user.get(base_url)["results"]

    assert len(got[0]["content"]["lecturers"]) == 5
