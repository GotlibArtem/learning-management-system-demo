import shutil
from collections.abc import Iterable

import pytest
from django.conf import settings


@pytest.fixture(scope="session", autouse=True)
def _temporary_media(tmpdir_factory: pytest.TempdirFactory) -> Iterable[None]:
    settings.MEDIA_ROOT = str(tmpdir_factory.mktemp("testmedia"))
    yield
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
