import os
from uuid import UUID

from app.files import RandomFileName


def test():
    file = "image.jpg"

    result = RandomFileName("dir/with/pictures")(None, file)

    path, filename = os.path.split(result)
    assert "dir/with/pictures" in path
    assert UUID(filename.split(".")[0])
