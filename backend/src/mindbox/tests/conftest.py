import pytest

from mindbox.services import MindboxClient


@pytest.fixture
def get_client():
    return lambda: MindboxClient()


@pytest.fixture(autouse=True)
def mock_mindbox_request(mocker):
    return mocker.patch(
        "app.convenient_http_client.ConvenientHTTPClient.request",
        return_value=({"status": "Success"}, 200),
    )


@pytest.fixture(autouse=True)
def adjust_settings(settings):
    settings.MINDBOX_ENABLED = True
    settings.MINDBOX_URL = "https://mindbox.comx/demo/"
    settings.MINDBOX_ENDPOINT_ID = "TheEndpoint"
    settings.MINDBOX_ENDPOINT_SECRET_KEY = "TheSecret"
