import uuid
from typing import Any, Protocol

from app.models import models
from main_page.models.main_page_content import MainPageContent


class BaseMainPageContent(Protocol):
    @property
    def main_page_content_id(self) -> uuid.UUID | None: ...

    @property
    def _main_page_content_type(self) -> str: ...


class MainPageContentParentLinkMixin(models.Model):
    """Use it for all content models to create proper back link to mother model."""

    _main_page_content_type: str

    main_page_content = models.OneToOneField(
        MainPageContent,
        on_delete=models.CASCADE,
        db_column="id",
        parent_link=True,
        primary_key=True,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True
        ordering = ["position_on_page", "created"]

    def save(self: BaseMainPageContent, *args: Any, **kwargs: Any) -> None:
        if self.main_page_content_id is None:
            self.main_page_content_type = self._main_page_content_type

        super().save(*args, **kwargs)  # type: ignore
