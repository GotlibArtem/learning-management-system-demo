import os
import uuid
from typing import Any

from django.utils.deconstruct import deconstructible


@deconstructible
class RandomFileName:
    """Random filename generator for model's FileField and ImageField. Example with specifying file path:
    image = models.ImageField(upload_to=RandomFileName('images/folder')
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def __call__(self, _: Any, filename: str) -> str:
        extension = os.path.splitext(filename)[1]  # noqa: PTH122

        return os.path.join(self.path, f"{uuid.uuid4()}{extension}")  # noqa: PTH118
