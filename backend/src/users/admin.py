from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as _UserAdmin
from django.db.transaction import on_commit
from django.http import HttpRequest
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from nested_admin import NestedModelAdmin, NestedTabularInline

from bonuses.models import BonusAccount, BonusTransaction
from payments.models import Payment, PaymentInstrument, Recurrent, RecurrentStatus
from product_access.models import ProductAccess
from users.models import User
from users.services import UserAllInterestsUpdater


class BonusTransactionInline(NestedTabularInline):
    model = BonusTransaction
    extra = 0
    can_delete = False
    show_change_link = False
    ordering = ["-created"]

    fields = ["amount", "transaction_type", "reason", "created_by", "created"]
    readonly_fields = ["amount", "transaction_type", "reason", "created_by", "created", "modified"]

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


class BonusAccountInline(NestedTabularInline):
    model = BonusAccount
    extra = 0
    can_delete = False
    fields = ["balance", "is_active", "bonus_actions"]
    readonly_fields = ["balance", "bonus_actions"]

    inlines = [BonusTransactionInline]

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def get_formset(self, request: HttpRequest, obj: Any | None = None, **kwargs: Any) -> Any:
        self._request = request
        return super().get_formset(request, obj, **kwargs)

    @admin.display(description=_("Actions with bonuses"))
    @mark_safe  # noqa: S308
    def bonus_actions(self, obj: Any | None = None) -> str:
        if not obj or not obj.pk:
            return "-"

        request = getattr(self, "_request", None)
        next_param = ""
        if request is not None and hasattr(request, "get_full_path"):
            next_param = "&" + urlencode({"next": request.get_full_path()})

        change_url = reverse("admin:bonuses_bonustransaction_add") + f"?account={obj.pk}{next_param}"

        return f'<a class="button" href="{change_url}">{_("Change bonuses")}</a>'


class UserPaymentInstrumentInline(NestedTabularInline):
    model = PaymentInstrument
    extra = 0
    can_delete = True
    fields = ["provider", "payment_method", "card_mask", "exp_date", "rebill_id", "status"]
    readonly_fields = ["provider", "payment_method", "card_mask", "exp_date", "rebill_id"]
    show_change_link = True
    ordering = ("-created",)

    def has_add_permission(self, request: HttpRequest, obj: PaymentInstrument | None = None) -> bool:
        return False


class UserRecurrentInline(NestedTabularInline):
    model = Recurrent
    extra = 0
    can_delete = False
    fields = ["product", "amount", "next_charge_date", "status"]
    readonly_fields = ["product"]
    show_change_link = True
    ordering = ("-next_charge_date",)

    def has_add_permission(self, request: HttpRequest, obj: Recurrent | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Recurrent | None = None) -> bool:
        return False


class UserPaymentInline(NestedTabularInline):
    model = Payment
    extra = 0
    can_delete = False
    fields = ["product", "source", "amount", "status", "paid_at", "is_recurrent"]
    readonly_fields = ["product", "source", "amount", "status", "paid_at", "is_recurrent"]
    show_change_link = True
    ordering = ("-paid_at",)

    def has_add_permission(self, request: HttpRequest, obj: Payment | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Payment | None = None) -> bool:
        return False


class UserProductAccessInline(NestedTabularInline):
    model = ProductAccess
    extra = 0
    can_delete = True
    fields = ["product", "start_date", "end_date"]
    readonly_fields = ["product", "start_date"]
    show_change_link = True
    ordering = ("-start_date",)

    def has_add_permission(self, request: HttpRequest, obj: ProductAccess | None = None) -> bool:
        return False


class HasRecurrentSubscriptionFilter(admin.SimpleListFilter):
    title = _("Recurrent subscription")
    parameter_name = "has_recurrent_subscription"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list:
        return [("yes", _("Yes")), ("no", _("No"))]

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        match self.value():
            case "yes":
                return queryset.filter(
                    recurrent_subscriptions__status=RecurrentStatus.ACTIVE,
                    recurrent_subscriptions__product__product_type="subscription",
                ).distinct()
            case "no":
                return queryset.exclude(
                    recurrent_subscriptions__status=RecurrentStatus.ACTIVE,
                    recurrent_subscriptions__product__product_type="subscription",
                ).distinct()
            case _:
                return queryset


class UserAdmin(NestedModelAdmin, _UserAdmin):
    fieldsets = (
        (None, {"fields": ("id", "username", "password", "login_as")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone")}),
        (_("User's interests"), {"fields": ("interests", "all_interests")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "email_confirmed_at")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
    )

    readonly_fields = ["id", "last_login", "date_joined", "login_as", "all_interests"]

    filter_horizontal = ("groups", "interests")

    list_display = ("id", "username", "email_confirmed_at", "bonus_account_balance", "bonus_account_actions", "has_recurrent_subscription")
    list_filter = [HasRecurrentSubscriptionFilter, "is_staff", "is_superuser", "is_active", "groups"]
    search_fields = ("id", "username", "first_name", "last_name")

    inlines = [UserPaymentInstrumentInline, UserRecurrentInline, UserPaymentInline, BonusAccountInline, UserProductAccessInline]

    def get_list_display(self, request: HttpRequest) -> Any:
        self._request = request
        return super().get_list_display(request)

    def get_inline_instances(self, request: HttpRequest, obj: User | None = None) -> list[NestedTabularInline]:
        inline_instances = []
        for inline_class in self.inlines:
            if inline_class is UserRecurrentInline and obj:
                if not obj.recurrent_subscriptions.exists():
                    continue
            if inline_class is UserPaymentInline and obj:
                if not obj.payments.exists():
                    continue
            if inline_class is UserProductAccessInline and obj:
                if not obj.product_access_items.exists():
                    continue
            inline_instances.append(inline_class(self.model, self.admin_site))
        return inline_instances

    def save_related(self, request: HttpRequest, form: Any, formsets: Any, change: bool) -> None:
        super().save_related(request, form, formsets, change)

        UserAllInterestsUpdater(user=form.instance)()

    @admin.display(description=_("Bonus account"))
    def bonus_account_balance(self, obj: User) -> str:
        account = getattr(obj, "bonus_account", None)
        if not account:
            return "—"
        return str(account.balance)

    @admin.display(description=_("Actions with bonuses"))
    @mark_safe  # noqa: S308
    def bonus_account_actions(self, obj: User) -> str:
        account = getattr(obj, "bonus_account", None)
        if not account:
            return str(_("No bonus account"))

        next_param = ""
        if hasattr(self, "_request") and self._request and hasattr(self._request, "get_full_path"):
            next_param = "&" + urlencode({"next": self._request.get_full_path()})

        change_url = reverse("admin:bonuses_bonustransaction_add") + f"?account={account.pk}{next_param}"

        return f'<a class="button" href="{change_url}">{_("Change bonuses")}</a>'

    @admin.display(description=_("Recurrent subscription"), boolean=True)
    def has_recurrent_subscription(self, obj: User) -> bool:
        return obj.recurrent_subscriptions.filter(status=RecurrentStatus.ACTIVE, product__product_type="subscription").exists()

    @admin.display(description=_("Login as user"))
    @mark_safe  # noqa: S308
    def login_as(self, obj: User) -> str:
        login_as_url = obj.get_login_as_url()
        return f'<a href="{login_as_url}" target="_blank">{_("Login as user")}</a>'


admin.site.register(User, UserAdmin)
