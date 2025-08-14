from collections.abc import Callable
from datetime import datetime

import pytest
from django.utils.timezone import make_aware


@pytest.fixture
def make_dt() -> Callable[[str], datetime]:
    """Make datetime with current time zone from strings like '2010-10-20 12:25:00'"""
    return lambda date_str: make_aware(datetime.fromisoformat(date_str if date_str[-1] != "Z" else date_str[:-1]))
