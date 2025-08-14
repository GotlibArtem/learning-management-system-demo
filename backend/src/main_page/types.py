from typing import TYPE_CHECKING, Union


if TYPE_CHECKING:
    from main_page.models import CategoriesContent, LecturersContent


MainPageContentType = Union["CategoriesContent", "LecturersContent"]
