import pytest


@pytest.fixture
def mock_auth_code_task(mocker):
    return mocker.patch("users.tasks.send_user_auth_code_to_email.delay")
