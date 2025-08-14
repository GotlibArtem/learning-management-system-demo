from app.admin import ModelAdmin, admin
from main_page.admin.course_bundle_content import CourseBundleContentAdmin
from main_page.admin.lecture_bundle_content import LectureBundleContentAdmin
from main_page.admin.main_page_content import CategoriesContentAdmin, LecturersContentAdmin, MainPageContentAdmin
from main_page.admin.main_page_recommendation import MainPageRecommendationAdmin


__all__ = [
    "CategoriesContentAdmin",
    "CourseBundleContentAdmin",
    "LectureBundleContentAdmin",
    "LecturersContentAdmin",
    "MainPageContentAdmin",
    "MainPageRecommendationAdmin",
    "ModelAdmin",
    "admin",
]
