from functools import cached_property
from urllib.parse import urljoin

import requests
from locust import HttpUser, between, tag, task

from app.conf.environ import env


class LMSUser(HttpUser):
    wait_time = between(0.5, 3)  # type: ignore[no-untyped-call]

    @task(weight=1)
    @tag("main_page")
    def main_page_recommendation(self) -> None:
        self.client.get("/api/demo/main-page/recommendations/", headers=self.headers)

    @task(weight=1)
    @tag("main_page")
    def lecture_progress(self) -> None:
        self.client.get("/api/demo/lectures-progress/", headers=self.headers)

    @task(weight=1)
    @tag("main_page")
    def main_page_content(self) -> None:
        self.client.get("/api/demo/main-page/content/", headers=self.headers)

    @task(weight=4)
    @tag("main_page")
    def main_page_course_bundle(self) -> None:
        self.client.get("/api/demo/main-page/course-bundles/", headers=self.headers)

    @task(weight=4)
    @tag("main_page")
    def main_page_lecture_bundle(self) -> None:
        self.client.get("/api/demo/main-page/lecture-bundles/", headers=self.headers)

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @cached_property
    def token(self) -> str:
        url = urljoin(self.client.base_url, "/api/demo/auth/token/obtain-by-password/")
        username = env("LMS_USER_NAME")
        password = env("LMS_USER_PASSWORD")
        return requests.post(
            url,
            json={"username": username, "password": password},
            timeout=60,
        ).json()["token"]
