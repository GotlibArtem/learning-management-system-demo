import zoneinfo
from datetime import datetime

import pytest

from users.models import User
from users.services import UserImporter, UserImporterException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def data():
    return {
        "Имя": "Ванесса",
        "Фамилия": "Мэй",
        "E-mail": "vm@gmail.test",
        "Телефон": None,
        "Дата регистрации": "2024-12-12T13:39:58.000Z",
        "Последний день подписки": "2025-12-12T12:41:05.187Z",
        "Реф.код": "33SS01",
    }


@pytest.fixture
def importer(data):
    return UserImporter(data=data)


@pytest.fixture
def user(factory):
    return factory.user(username="vm@gmail.test")


def test_new_user_is_created(importer):
    importer()

    user = User.objects.get()
    assert user.username == "vm@gmail.test"
    assert user.email == "vm@gmail.test"
    assert user.first_name == "Ванесса"
    assert user.last_name == "Мэй"
    assert user.date_joined == datetime(2024, 12, 12, 13, 39, 58, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert user.avatar_slug == "abstract"


@pytest.mark.parametrize("username", ["vm@gmail.test", "  vm@gmail.TESt  "])
def test_update_existing_user(importer, user, data, username):
    data["E-mail"] = username

    importer()

    user.refresh_from_db()
    assert user.username == "vm@gmail.test"
    assert user.email == "vm@gmail.test"
    assert user.first_name == "Ванесса"
    assert user.last_name == "Мэй"
    assert user.date_joined == datetime(2024, 12, 12, 13, 39, 58, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert user.avatar_slug == "abstract"


def test_validate_email(importer, data):
    data["E-mail"] = "invalid-email"

    with pytest.raises(UserImporterException, match="invalid email"):
        importer()


@pytest.mark.parametrize("username", ["vm@gmail.test ", "  vm@gmail.test", "VM@gmail.TEST"])
def test_formatting_username(importer, data, username):
    data["E-mail"] = username

    user = importer()

    assert user.username == "vm@gmail.test"
    assert user.email == "vm@gmail.test"


@pytest.mark.parametrize("first_name", ["Ванесса ", "  Ванесса"])
def test_formatting_first_name(importer, data, first_name):
    data["Имя"] = first_name

    user = importer()

    assert user.first_name == "Ванесса"


@pytest.mark.parametrize("last_name", ["Мэй ", "  Мэй"])
def test_formatting_last_name(importer, data, last_name):
    data["Фамилия"] = last_name

    user = importer()

    assert user.last_name == "Мэй"


def test_skip_existing_user_updating(importer, user):
    importer.skip_if_user_exists = True

    importer()

    user.refresh_from_db()
    assert user.first_name != "Ванесса"
