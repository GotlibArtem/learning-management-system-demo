from typing import TYPE_CHECKING, ClassVar
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as _UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import DefaultModel


if TYPE_CHECKING:
    from product_access.services import SubscriptionBoundaries


class User(AbstractUser, DefaultModel):
    objects: ClassVar[_UserManager] = _UserManager()

    phone = models.CharField(
        _("Phone"),
        max_length=32,
        blank=True,
        default="",
        help_text=_("User's phone number"),
    )
    email_confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Email confirmed at"),
    )
    birthdate = models.DateField(
        _("Birthdate"),
        null=True,
        blank=True,
    )
    avatar_slug = models.SlugField(
        _("Avatar slug"),
        blank=True,
        choices=[
            ("abstract", "abstract"),
            ("apollo", "apollo"),
            ("caravaggio", "caravaggio"),
            ("cat", "cat"),
            ("cat2", "cat2"),
            ("frida", "frida"),
            ("indian", "indian"),
            ("joker", "joker"),
            ("lakoon", "lakoon"),
            ("medieval", "medieval"),
            ("rafael", "rafael"),
            ("rossetti", "rossetti"),
            ("thinker", "thinker"),
            ("venus", "venus"),
            ("venus2", "venus2"),
            ("woman", "woman"),
        ],
    )

    rhash = models.CharField(_("Rhash"), max_length=256, blank=True)

    # User's interests
    interests = models.ManyToManyField(
        "courses.Category",
        blank=True,
        related_name="users",
        verbose_name=_("Interests"),
        help_text=_("User's selected interests"),
    )
    all_interests = models.BooleanField(
        _("All interests selected"),
        default=False,
        help_text=_("Whether the user has selected all interests"),
    )

    has_accepted_data_consent = models.BooleanField(
        _("Has accepted data consent in the App"),
        null=True,
        blank=True,
        help_text=_("Whether the user has accepted data consent in the App"),
    )

    class Meta:
        permissions = [
            ("allow_mindbox_integration", _("Can send integration requests from the mindbox")),
        ]
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    @property
    def subscription_boundaries(self) -> "SubscriptionBoundaries | None":
        from product_access.services import SubscriptionBoundariesCalculator

        return SubscriptionBoundariesCalculator(user=self).get_any_subscription_boundaries()

    def get_login_as_url(self) -> str:
        return urljoin(settings.ABSOLUTE_URL, f"/auth/as/{self.pk}/")

    def has_recurring_subscription(self) -> bool:
        from product_access.services import UserRecurringSubscriptionChecker

        return UserRecurringSubscriptionChecker(user=self)()

    def is_apple_review_account(self) -> bool:
        return self.email in [
            settings.APPLE_REVIEW_ACCOUNT_EMAIL,
            settings.APPLE_REVIEW_ACCOUNT_EMAIL_2,
            settings.APPLE_REVIEW_ACCOUNT_EMAIL_3,
        ]
