from dataclasses import dataclass

from django.db.transaction import atomic

from app.services import BaseService
from mindbox.decorators import mindbox_enabled
from mindbox.services.client import MindboxClient
from mindbox.types import CourseProgressStatus


COMPLETED_PERCENT = 100


@dataclass
class MindboxProgressNotifier(BaseService):
    course_progress: dict

    def __post_init__(self) -> None:
        self.mindbox_client = MindboxClient()

    @mindbox_enabled
    def act(self) -> None:
        if not self.should_send:
            return

        is_first_progress = self.course_progress.mindbox_sent_percent is None
        if is_first_progress:
            with atomic():
                self.mindbox_client.course_started(
                    email=self.course_progress.user.username,
                    progress_id=str(self.course_progress.id),
                    product_id=self.shop_id,
                )
                self.course_progress.mindbox_sent_percent = 0
                self.course_progress.save(update_fields=["mindbox_sent_percent", "modified"])

        current_status = self._get_status(self.current_progress)
        previous_status = self._get_status(self.previous_progress)
        has_status_changed = current_status != previous_status
        has_progress_increased = self.current_progress > self.previous_progress
        is_newly_completed = current_status == CourseProgressStatus.FINISHED and self.previous_progress < COMPLETED_PERCENT
        if has_status_changed and has_progress_increased:
            with atomic():
                self.mindbox_client.update_course_progress(
                    progress_id=str(self.course_progress.id),
                    status=current_status,
                )
                if is_newly_completed:
                    self.mindbox_client.add_course_to_watched(
                        email=self.course_progress.user.username,
                        product_id=self.shop_id,
                    )
                self.course_progress.mindbox_sent_percent = self.course_progress.completion_percent
                self.course_progress.save(update_fields=["mindbox_sent_percent", "modified"])

    def _get_status(self, percent: int) -> CourseProgressStatus:
        result = CourseProgressStatus.PROGRESS_1
        if percent >= COMPLETED_PERCENT:
            result = CourseProgressStatus.FINISHED
        elif percent >= 90:  # noqa: PLR2004
            result = CourseProgressStatus.PROGRESS_90
        elif percent >= 75:  # noqa: PLR2004
            result = CourseProgressStatus.PROGRESS_75
        elif percent >= 50:  # noqa: PLR2004
            result = CourseProgressStatus.PROGRESS_50
        elif percent >= 25:  # noqa: PLR2004
            result = CourseProgressStatus.PROGRESS_25
        elif percent >= 10:  # noqa: PLR2004
            result = CourseProgressStatus.PROGRESS_10
        elif percent >= 5:  # noqa: PLR2004
            result = CourseProgressStatus.PROGRESS_5
        return result

    @property
    def current_progress(self) -> int:
        return self.course_progress.completion_percent

    @property
    def previous_progress(self) -> int:
        return self.course_progress.mindbox_sent_percent  # type: ignore
