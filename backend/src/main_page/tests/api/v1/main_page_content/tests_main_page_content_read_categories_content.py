import pytest


pytestmark = [
    pytest.mark.django_db,
]


base_url = "/api/demo/main-page/content/"


@pytest.fixture(autouse=True)
def categories_content(factory):
    return factory.categories_content(
        name="Наши направляшки",
        is_hidden=False,
    )


def test_read(as_user, categories_content):
    got = as_user.get(base_url)["results"]

    assert len(got) == 1

    got = got[0]
    assert got["id"] == str(categories_content.id)
    assert got["mainPageContentType"] == "categories-content"


def test_content(as_user, categories_content):
    got = as_user.get(base_url)["results"]

    content = got[0]["content"]
    assert content["name"] == "Наши направляшки"
    assert "categories" in content


def test_read_categories_list(as_user, factory):
    factory.cycle(3).category()

    got = as_user.get(base_url)["results"]

    categories = got[0]["content"]["categories"]
    assert len(categories) == 3


def test_read_list_categories_fields(as_user, category):
    got = as_user.get(base_url)["results"]

    category_data = got[0]["content"]["categories"][0]
    assert category_data["name"] == category.name
    assert category_data["slug"] == category.slug
