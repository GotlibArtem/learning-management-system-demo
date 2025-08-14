from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel


class CorporateEmailDomain(TimestampedModel):
    """
    Represents an email domain considered corporate for Mindbox logic.
    """

    domain = models.CharField(
        _("Email domain"),
        max_length=255,
        unique=True,
        help_text=_("Domain part of the email address"),
    )

    class Meta:
        verbose_name = _("Corporate email domain")
        verbose_name_plural = _("Corporate email domains")
        ordering = ["domain"]

    def __str__(self) -> str:
        return self.domain
