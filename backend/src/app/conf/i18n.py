from pathlib import Path

from app.conf.boilerplate import BASE_DIR


LANGUAGE_CODE = "en"

LOCALE_PATHS = [Path(BASE_DIR).parent / "_locale"]

USE_i18N = True
