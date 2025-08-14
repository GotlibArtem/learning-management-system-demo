import uuid
from typing import Any

from behaviors.behaviors import Timestamped
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


__all__ = [
    "DefaultModel",
    "TimestampedModel",
    "models",
]


class DefaultModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        """Default name for all models"""
        name = getattr(self, "name", None)
        if name is not None:
            return str(name)

        return super().__str__()

    @classmethod
    def get_contenttype(cls) -> ContentType:
        return ContentType.objects.get_for_model(cls)

    def update_from_kwargs(self, **kwargs: dict[str, Any]) -> None:
        """A shortcut method to update model instance from the kwargs."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def setattr_and_save(self, key: str, value: Any) -> None:
        """Shortcut for testing -- set attribute of the model and save"""
        setattr(self, key, value)
        self.save()

    @classmethod
    def get_label(cls) -> str:
        """Get a unique within the app model label"""
        return cls._meta.label_lower.split(".")[-1]


class TimestampedModel(DefaultModel, Timestamped):
    """
    Default app model that has `created` and `updated` attributes.
    Currently based on https://github.com/audiolion/django-behaviors
    """

    class Meta:
        abstract = True


class ShopDeadLetter(TimestampedModel):
    event_type = models.CharField(max_length=32, db_index=True)
    raw_data = models.JSONField(default=dict)
    details = models.TextField(help_text=_("Error details"), blank=True, default="")

    class Meta:
        verbose_name = _("Shop dead letter")
        verbose_name_plural = _("Shop dead letters")
        ordering = ["created"]

    def __str__(self) -> str:
        return f"{self.event_type} {self.created}"
