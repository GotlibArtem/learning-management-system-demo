import pytest


@pytest.fixture
def mock_mindbox(mocker):  # type: ignore
    return mocker.patch("mindbox.services.client.MindboxClient.run_email_operation")
