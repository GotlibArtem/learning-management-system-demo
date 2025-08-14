import pytest
import requests_mock
from requests.exceptions import RequestException

from app.convenient_http_client import ConvenientHTTPClient


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def get_client():
    with requests_mock.Mocker() as http_mock:

        def _get_client(base_url):
            client = ConvenientHTTPClient(base_url=base_url)
            client.m = http_mock
            return client

        yield _get_client


@pytest.fixture
def client(get_client):
    return get_client("http://localhost:777/v0/api")


def test_post_request(client):
    client.m.post("http://localhost:777/v0/api/requests/100500", json={"receipt": "data"})

    result, status = client.request(method="post", endpoint="requests/100500", data={"content": "some"})

    assert result == {"receipt": "data"}
    assert status == 200
    assert client.m.last_request.json()["content"] == "some"


def test_get_request(client):
    client.m.get("http://localhost:777/v0/api/requests/100500", json={"receipt": "data"})

    result, status = client.request(method="get", endpoint="requests/100500")

    assert result == {"receipt": "data"}
    assert status == 200


def test_allow_get_params_in_endpoint(client):
    client.m.get("http://localhost:777/v0/api/requests/100500?what=is&love=true", json={"receipt": "data"})

    result, status = client.request(method="get", endpoint="requests/100500?what=is&love=true")

    assert result == {"receipt": "data"}
    assert status == 200


def test_raise_on_request_errors(client):
    client.m.get("http://localhost:777/v0/api/requests/100500", json={"receipt": "data"}, status_code=400)

    with pytest.raises(RequestException):
        client.request(method="get", endpoint="requests/100500", data={"data": "here"})


def test_do_not_raise_on_request_errors_if_enabled(client):
    client.m.get("http://localhost:777/v0/api/requests/100500", json={"receipt": "data"}, status_code=400)

    result, status = client.request(method="get", endpoint="requests/100500", data={"data": "here"}, raise_for_status=False)

    assert result == {"receipt": "data"}
    assert status == 400


def test_do_not_raise_on_empty_body_response(client):
    client.m.get("http://localhost:777/v0/api/requests/100500", status_code=201)

    result, status = client.request(method="get", endpoint="requests/100500")

    assert result == {}
    assert status == 201


def test_default_headers(client):
    client.m.post("http://localhost:777/v0/api/default-url", json={"default": "response"})

    client.request(method="post", endpoint="default-url")

    headers = client.m.last_request.headers
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"


def test_updated_headers(client):
    client.m.post("http://localhost:777/v0/api/default-url", json={"default": "response"})

    client.request(method="post", endpoint="default-url", headers={"Accept": "application/xml"})

    headers = client.m.last_request.headers
    assert headers["Accept"] == "application/xml"
    assert headers["Content-Type"] == "application/json"


def test_additional_headers(client):
    client.m.post("http://localhost:777/v0/api/default-url", json={"default": "response"})

    client.request(method="post", endpoint="default-url", headers={"Authorization": "secretkey topsecr3t"})

    headers = client.m.last_request.headers
    assert headers["Authorization"] == "secretkey topsecr3t"
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.parametrize(
    "base_url",
    [
        "http://localhost:777/v0/api",
        "http://localhost:777/v0/api/",
    ],
)
def test_smart_slash_concat_to_base_url(get_client, base_url):
    client = get_client(base_url)
    client.m.put("http://localhost:777/v0/api/someboy", json={"some": "response"})

    result, status = client.request(method="put", endpoint="someboy")

    assert result == {"some": "response"}
    assert status == 200
