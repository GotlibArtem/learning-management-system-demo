from datetime import date

import pytest

from users.services import UserCreator
from users.services.user_creator import UserCreatorException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def create_user():
    return lambda data: UserCreator(**data)()


@pytest.fixture
def data():
    return {
        "username": "some@asd.good",
    }


@pytest.fixture(autouse=True)
def mock_register_customer_task(mocker):
    return mocker.patch("mindbox.tasks.register_customer.delay")


def test_create_user_with_just_only_username(create_user, data):
    user = create_user(data)

    user.refresh_from_db()
    assert user.username == "some@asd.good"
    assert user.email == "some@asd.good"
    assert user.phone == ""
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.email_confirmed_at is None
    assert user.birthdate is None
    assert user.avatar_slug == ""


def test_create_user_with_all_data(create_user, data):
    data["phone"] = "79999999999"
    data["first_name"] = "Besik"
    data["last_name"] = "Rushkevich"
    data["birthdate"] = date(1995, 2, 3)
    data["avatar_slug"] = "abstract"

    user = create_user(data)

    user.refresh_from_db()
    assert user.phone == "+79999999999"
    assert user.first_name == "Besik"
    assert user.last_name == "Rushkevich"
    assert user.birthdate == date(1995, 2, 3)
    assert user.avatar_slug == "abstract"


def test_impossible_to_create_if_user_with_username_already_exists(create_user, data):
    create_user(data)

    with pytest.raises(UserCreatorException, match="User with such email already exists."):
        create_user(data)


@pytest.mark.parametrize("username", ["aSd@asd.coM", "   aSd@asd.coM   "])
def test_normalizer_username(create_user, data, username):
    data["username"] = username

    user = create_user(data)

    user.refresh_from_db()
    assert user.username == "asd@asd.com"


@pytest.mark.parametrize("username", ["not-an-email", "фывы@asd.com", "1324asd.com", " "])
def test_impossible_to_create_if_bad_username(create_user, data, username):
    data["username"] = username

    with pytest.raises(UserCreatorException, match="Invalid email."):
        create_user(data)


@pytest.mark.parametrize("field", ["username"])
def test_impossible_to_create_without_field(create_user, data, field):
    del data[field]

    with pytest.raises(TypeError, match="missing"):
        create_user(data)


@pytest.mark.parametrize("field", ["username"])
def test_impossible_to_create_if_field_is_none(create_user, data, field):
    data[field] = None

    with pytest.raises(UserCreatorException, match="required"):
        create_user(data)


def test_create_user_with_rhash(create_user, data):
    data["rhash"] = "test_rhash"

    user = create_user(data)

    user.refresh_from_db()
    assert user.rhash == "test_rhash"


def test_register_customer_task_is_called(create_user, data, mock_register_customer_task, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        user = create_user(data)

    mock_register_customer_task.assert_called_once_with(str(user.id))
