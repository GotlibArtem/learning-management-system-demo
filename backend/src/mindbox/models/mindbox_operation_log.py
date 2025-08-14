from django.db import models
from django.utils.translation import gettext_lazy as _

from app.json_encoders import AppJSONEncoder
from app.models import TimestampedModel


class MindboxOperationLog(TimestampedModel):
    """
    Stores information about each operation sent to the Mindbox API.
    """

    operation = models.CharField(_("Mindbox operation name"), max_length=64, db_index=True)
    destination = models.CharField(_("Destination"), max_length=512, blank=True, db_index=True)
    content = models.JSONField(_("Content"), encoder=AppJSONEncoder)

    class Meta:
        verbose_name = _("Mindbox operation log")
        verbose_name_plural = _("Mindbox operation log entries")
