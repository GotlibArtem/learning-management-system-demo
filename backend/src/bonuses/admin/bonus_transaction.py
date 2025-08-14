import uuid
from typing import Any

from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from app.admin import ModelAdmin
from bonuses.models import BonusAccount, BonusTransaction, BonusTransactionType
from bonuses.services import BonusTransactionCreator


@admin.register(BonusTransaction)
class BonusTransactionAdmin(ModelAdmin):
    list_display = ["account", "amount", "transaction_type", "reason", "created_by", "created"]
    list_filter = ["transaction_type", "created"]

    search_fields = [
        "account__user__email",
        "account__user__username",
        "account__user__id",
        "amount",
        "reason",
    ]
    readonly_fields = ["created", "modified"]
    ordering = ["-created"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return bool(request.GET.get("account"))

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return obj is None

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def get_form(self, request: HttpRequest, obj: Any | None = None, change: bool = False, **kwargs: Any) -> type[ModelForm]:
        self._request = request
        return super().get_form(request, obj, change=change, **kwargs)

    def get_model_perms(self, request: HttpRequest) -> dict:
        """Hide model from the admin index and app list."""
        return {}

    def formfield_for_choice_field(self, db_field: Any, request: HttpRequest, **kwargs: Any) -> Any:
        if db_field.name == "transaction_type":
            allowed = [
                (BonusTransactionType.ADMIN_EARNED, BonusTransactionType.ADMIN_EARNED.label),
                (BonusTransactionType.ADMIN_SPENT, BonusTransactionType.ADMIN_SPENT.label),
            ]
            kwargs["choices"] = allowed
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_fields(self, request: HttpRequest, obj: Any | None = None) -> tuple[str, ...]:
        if obj:
            return ("account", "transaction_type", "amount", "reason", "created_by", "created", "modified")

        if request.GET.get("account"):
            return ("user", "transaction_type", "amount", "future_balance", "reason")

        return ("account", "transaction_type", "amount", "future_balance", "reason")

    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = None) -> tuple[str, ...]:
        if obj:
            return ("account", "transaction_type", "amount", "reason", "created_by", "created", "modified")

        if request.GET.get("account"):
            return ("user", "future_balance", "created", "modified")

        return ("future_balance", "created", "modified")

    def response_add(self, request: HttpRequest, obj: Any, post_url_continue: str | None = None) -> HttpResponse:
        next_url = request.GET.get("next")
        if next_url:
            return HttpResponseRedirect(next_url)

        return HttpResponseRedirect(reverse("admin:users_user_changelist"))

    def save_model(self, request: HttpRequest, obj: Any, form: Any, change: bool) -> None:
        if not change:
            account_id = request.GET.get("account")

            if account_id:
                account = BonusAccount.objects.get(pk=account_id)
                obj.account = account

            obj.created_by = request.user if request.user.is_authenticated else None

            if obj.transaction_type in [BonusTransactionType.SPENT, BonusTransactionType.ADMIN_SPENT]:
                obj.amount = -abs(obj.amount)
            else:
                obj.amount = abs(obj.amount)

            super().save_model(request, obj, form, change)

            BonusTransactionCreator(
                email=obj.account.user.email,
                amount=abs(obj.amount),
                transaction_type=obj.transaction_type,
                reason=obj.reason,
                created_by=obj.created_by,
            ).update_balance(obj.account)
            return

        super().save_model(request, obj, form, change)

    @admin.display(description=_("User"))
    def user(self, obj: Any = None) -> str:
        request = getattr(self, "_request", None)
        if not request:
            return ""

        account_id = request.GET.get("account")
        if not account_id:
            return ""

        account = BonusAccount.objects.select_related("user").get(pk=uuid.UUID(account_id))
        return str(account.user)

    @admin.display(description=_("Balance"))
    @mark_safe  # noqa: S308
    def future_balance(self, obj: Any = None) -> str:
        request = getattr(self, "_request", None)
        if not request:
            return ""

        account_id = request.GET.get("account")
        if not account_id:
            return ""

        account = BonusAccount.objects.get(pk=account_id)

        return (
            f"<span style='margin-right:1em;'>Текущий: <b id='current-balance'>{account.balance}</b></span>"
            f"<span style='margin: 0 1.5em;'>→</span>"
            f"Будущий: <b id='future-balance' data-orig='{account.balance}'>{account.balance}</b>"
        )

    class Media:
        js = ("bonuses/admin/js/bonus_future_balance.js",)
