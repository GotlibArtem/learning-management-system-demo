from datetime import date

import pytest
from django.db import IntegrityError

from users.models import User
from users.services import UserEditor, UserEditorException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def user(user):
    user.username = "some@email.test"
    user.email = "some@email.test"
    user.phone = "+79999999999"
    user.first_name = "John"
    user.last_name = "Doe"
    user.birthdate = date(1990, 3, 4)
    user.avatar_slug = "woman"
    user.save()
    return user


@pytest.fixture(autouse=True)
def mock_edit_customer_task(mocker):
    return mocker.patch("mindbox.tasks.edit_customer.delay")


@pytest.fixture
def editor():
    return UserEditor(
        username="some@email.test",
        phone="+79999999999",
        first_name="User",
        last_name="Userov",
        birthdate=date(1995, 2, 5),
        avatar_slug="abstract",
    )


def test_nonexistent_user_is_created(editor):
    editor()

    user = User.objects.get()
    assert user.email == "some@email.test"
    assert user.phone == "+79999999999"
    assert user.username == "some@email.test"
    assert user.first_name == "User"
    assert user.last_name == "Userov"
    assert user.birthdate == date(1995, 2, 5)
    assert user.avatar_slug == "abstract"


def test_nonexistent_user_with_default_values_is_created():
    UserEditor(username="some@email.test")()

    user = User.objects.get()
    assert user.email == "some@email.test"
    assert user.username == "some@email.test"
    assert user.phone == ""
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.birthdate is None
    assert user.avatar_slug == ""


def test_existent_user_is_updated(user, editor):
    editor()

    user.refresh_from_db()
    assert user.phone == "+79999999999"
    assert user.first_name == "User"
    assert user.last_name == "Userov"
    assert user.birthdate == date(1995, 2, 5)
    assert user.avatar_slug == "abstract"


def test_nullable_fields(user):
    UserEditor(
        username=user.username,
        phone=None,
        first_name=None,
        last_name=None,
        birthdate=None,
        avatar_slug=None,
    )()

    user.refresh_from_db()
    assert user.phone == ""
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.birthdate is None
    assert user.avatar_slug == ""


def test_return_value_for_new_user(editor):
    user, is_created = editor()

    assert user == User.objects.get()
    assert is_created is True


def test_return_value_for_existent_user(editor, user):
    user, is_created = editor()

    assert user == User.objects.get()
    assert is_created is False


def test_skip_updating_for_empty_value(editor, user):
    editor.phone = editor.empty_value
    editor.first_name = editor.empty_value
    editor.last_name = editor.empty_value
    editor.birthdate = editor.empty_value
    editor.avatar_slug = editor.empty_value

    editor()

    user.refresh_from_db()
    assert user.phone == "+79999999999"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.birthdate == date(1990, 3, 4)
    assert user.avatar_slug == "woman"


def test_do_not_update_anything_by_default(user):
    UserEditor(username=user.username)()

    user.refresh_from_db()
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.birthdate == date(1990, 3, 4)
    assert user.avatar_slug == "woman"


@pytest.mark.freeze_time("2020-02-02")
def test_error_if_birthdate_is_in_the_past(editor):
    editor.birthdate = date(2021, 1, 1)

    with pytest.raises(UserEditorException, match="born yet"):
        editor()


def test_handling_race_condition_on_user_creation(mocker, factory, editor):
    user = factory.user(username="some@email.test", email="some@email.test")

    mocker.patch(
        "users.services.user_editor.UserCreator.__call__",
        side_effect=[
            IntegrityError("duplicate key value violates unique constraint users_user_username_key"),
            user,
        ],
    )

    user, is_created = editor()

    assert is_created is False
    assert user.email == "some@email.test"
    assert user.username == "some@email.test"
    assert user.first_name == "User"
    assert user.last_name == "Userov"
    assert user.birthdate == date(1995, 2, 5)
    assert user.avatar_slug == "abstract"


@pytest.mark.parametrize("username", ["SOMe@email.test", " some@email.test "])
def test_getting_user_with_normalized_username(editor, username, user):
    editor.username = username

    editor()

    user.refresh_from_db()
    user.first_name = "User"


def test_user_with_rhash_is_created():
    editor = UserEditor(username="rhash_user@test.com", rhash="test_rhash")
    editor()

    user = User.objects.get(username="rhash_user@test.com")
    assert user.rhash == "test_rhash"


def test_update_user_rhash(user):
    editor = UserEditor(username=user.username, rhash="new_rhash")

    editor()

    user.refresh_from_db()
    assert user.rhash == "new_rhash"


def test_edit_customer_task_is_called(user, mock_edit_customer_task, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        UserEditor(username=user.username)()

    mock_edit_customer_task.assert_called_once_with(str(user.id))
