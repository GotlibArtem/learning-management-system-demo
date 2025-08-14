import pytest
from django.db import InternalError, OperationalError

from app.exceptions import AppDatabaseException
from app.models import ShopDeadLetter
from product_access.api.demo.decorators import dead_letter_creation


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def func_mock(mocker):
    return mocker.MagicMock()


@pytest.fixture
def http_request(mocker):
    mock = mocker.MagicMock()
    mock.data = {"test": "data"}
    return mock


@pytest.fixture
def call(func_mock, mocker, http_request):
    decorator = dead_letter_creation("test-event")
    return lambda: decorator(func_mock)(mocker.MagicMock(), http_request)


def test_decorated_func_is_called(call, func_mock):
    call()

    func_mock.assert_called_once()


def test_dead_letter_saving_on_error(call, func_mock):
    func_mock.side_effect = Exception("Oops, error!")

    with pytest.raises(Exception, match="Oops, error!"):
        call()

    dead_letter = ShopDeadLetter.objects.get()
    assert dead_letter.event_type == "test-event"


@pytest.mark.parametrize("error_class", [InternalError, OperationalError])
def test_handling_database_error(call, func_mock, error_class):
    func_mock.side_effect = error_class("db error")

    with pytest.raises(AppDatabaseException, match="db error"):
        call()
