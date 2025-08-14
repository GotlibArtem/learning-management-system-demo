import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import Token

from a12n.models import PasswordlessEmailAuthCode
from a12n.services.token_by_code_generator import TokenGeneratorByCode, TokenGeneratorByCodeException


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def inactive_user(factory):
    return factory.user(is_active=False)


@pytest.fixture
def auth_code(user):
    return PasswordlessEmailAuthCode.objects.create(
        user=user,
        code="123457",
        expires=timezone.now() + timezone.timedelta(minutes=5),
    )


@pytest.fixture(autouse=True)
def mock_notify_task(mocker):
    return mocker.patch("mindbox.tasks.notify_user_logged_in.delay")


@pytest.fixture
def service(user, auth_code):
    return TokenGeneratorByCode(username=user.username, code=auth_code.code, device_uuid="device-123")


def test_successful_token_generation(service, user, auth_code):
    token = service()

    auth_code.refresh_from_db()
    user.refresh_from_db()
    assert isinstance(token, Token)
    assert token["user_id"] == str(user.id)
    assert auth_code.used is not None
    assert user.email_confirmed_at is not None


def test_call_notify_task(service, user, mock_notify_task, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        service()

    mock_notify_task.assert_called_once_with(str(user.id), "device-123")


def test_not_call_notify_task_if_device_uuid_is_empty(service, user, mock_notify_task, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        service()

    mock_notify_task.assert_called_once_with(str(user.id), "device-123")


def test_no_notification_without_device_uuid(service, mock_notify_task):
    service.device_uuid = ""

    service()

    mock_notify_task.assert_not_called()


def test_case_insensitive_username(user, service):
    service.username = user.username.upper()

    token = service()

    assert isinstance(token, Token)
    assert token["user_id"] == str(user.id)


def test_nonexistent_user():
    service = TokenGeneratorByCode(username="nonexistent", code="123456", device_uuid="")

    with pytest.raises(TokenGeneratorByCodeException, match="Account does not exist"):
        service()


def test_inactive_user(service, inactive_user):
    service.username = inactive_user.username

    with pytest.raises(TokenGeneratorByCodeException, match="Inactive user"):
        service()


def test_invalid_code(service):
    service.code = "invalid"

    with pytest.raises(TokenGeneratorByCodeException, match="Invalid code"):
        service()


def test_expired_code(user, service):
    PasswordlessEmailAuthCode.objects.create(
        user=user,
        code="123456",
        expires=timezone.now() - timezone.timedelta(minutes=5),
    )
    service.code = "123456"

    with pytest.raises(TokenGeneratorByCodeException, match="Invalid code"):
        service()


def test_used_code(user, service):
    code = PasswordlessEmailAuthCode.objects.create(
        user=user,
        code="123456",
        expires=timezone.now() + timezone.timedelta(minutes=5),
        used=timezone.now(),
    )
    service.code = code.code

    with pytest.raises(TokenGeneratorByCodeException, match="Invalid code"):
        service()
