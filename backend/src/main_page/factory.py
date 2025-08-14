import uuid
from typing import Any

from app.testing import register
from app.testing.types import FactoryProtocol
from main_page.models import (
    CategoriesContent,
    CourseBundleContent,
    CourseBundleItem,
    LectureBundleContent,
    LectureBundleItem,
    LecturersContent,
    MainPageRecommendation,
)


@register
def main_page_recommendation(self: FactoryProtocol, **kwargs: Any) -> MainPageRecommendation:
    return self.mixer.blend(MainPageRecommendation, **kwargs)


@register
def lecturers_content(self: FactoryProtocol, **kwargs: dict) -> LecturersContent:
    kwargs["main_page_content"] = self.mixer.SKIP
    kwargs["main_page_content_type"] = self.mixer.SKIP

    return self.mixer.blend("main_page.LecturersContent", **kwargs)


@register
def categories_content(self: FactoryProtocol, **kwargs: dict) -> CategoriesContent:
    kwargs["main_page_content"] = self.mixer.SKIP
    kwargs["main_page_content_type"] = self.mixer.SKIP

    return self.mixer.blend("main_page.CategoriesContent", **kwargs)


@register
def course_bundle_content(self: FactoryProtocol, **kwargs: Any) -> CourseBundleContent:
    kwargs["main_page_content"] = self.mixer.SKIP
    kwargs["main_page_content_type"] = self.mixer.SKIP
    kwargs.setdefault("slug", str(uuid.uuid4()))

    return self.mixer.blend("main_page.CourseBundleContent", **kwargs)


@register
def lecture_bundle_content(self: FactoryProtocol, **kwargs: Any) -> LectureBundleContent:
    kwargs["main_page_content"] = self.mixer.SKIP
    kwargs["main_page_content_type"] = self.mixer.SKIP
    kwargs.setdefault("slug", str(uuid.uuid4()))

    return self.mixer.blend("main_page.LectureBundleContent", **kwargs)


@register
def lecture_bundle_item(self: FactoryProtocol, **kwargs: dict) -> LectureBundleItem:
    return self.mixer.blend("main_page.LectureBundleItem", **kwargs)


@register
def course_bundle_item(self: FactoryProtocol, **kwargs: dict) -> CourseBundleItem:
    return self.mixer.blend("main_page.CourseBundleItem", **kwargs)
