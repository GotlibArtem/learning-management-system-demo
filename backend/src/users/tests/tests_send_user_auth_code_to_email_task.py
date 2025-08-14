import pytest

from a12n.models import PasswordlessEmailAuthCode
from mindbox.models import CorporateEmailDomain
from users.tasks import send_user_auth_code_to_email


pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("mock_mindbox")]


@pytest.fixture(autouse=True)
def mock_context_builder(mocker):
    return mocker.patch("users.services.auth_code_email_context_builder.AuthCodeEmailContextBuilder.act", return_value={"a": "b"}, autospec=True)


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.MINDBOX_EMAIL_AUTH_CODE_OPERATION_NAME = "RegularOperation"
    settings.MINDBOX_EMAIL_AUTH_CODE_OPERATION_NAME_CORPORATE = "CorporateOperation"


@pytest.fixture
def auth_code(user):
    return PasswordlessEmailAuthCode.objects.create(user=user)


def test_call_mindbox_in_task(auth_code, mock_mindbox):
    send_user_auth_code_to_email(auth_code.id)

    mock_mindbox.assert_called_once()


def test_call_with_proper_operation_name(auth_code, mock_mindbox):
    send_user_auth_code_to_email(auth_code.id)

    assert mock_mindbox.call_args[0][0] == "RegularOperation"


def test_call_with_proper_email_parameter(user, auth_code, mock_mindbox):
    send_user_auth_code_to_email(auth_code.id)

    assert mock_mindbox.call_args[0][1] == user.username


def test_call_with_proper_mailing_context(auth_code, mock_mindbox):
    send_user_auth_code_to_email(auth_code.id)

    mailing_context = mock_mindbox.call_args[0][2]
    assert mailing_context == {"a": "b"}


def test_call_context_with_proper_params(auth_code, user, mock_context_builder):
    send_user_auth_code_to_email(auth_code.id)

    assert mock_context_builder.call_count == 1
    assert mock_context_builder.call_args[0][0].email == user.username
    assert mock_context_builder.call_args[0][0].code == auth_code.code


def test_corporate_domain_uses_corporate_operation_name(user, auth_code, mock_mindbox):
    domain = user.username.split("@")[-1]
    CorporateEmailDomain.objects.create(domain=domain)

    send_user_auth_code_to_email(auth_code.id)

    assert mock_mindbox.call_args[0][0] == "CorporateOperation"


def test_non_corporate_domain_uses_regular_operation_name(user, auth_code, mock_mindbox):
    send_user_auth_code_to_email(auth_code.id)

    assert mock_mindbox.call_args[0][0] == "RegularOperation"
