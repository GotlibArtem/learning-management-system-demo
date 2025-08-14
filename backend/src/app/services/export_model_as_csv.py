import csv
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.db.models import Model, QuerySet
from django.db.models.options import Options
from django.http import StreamingHttpResponse
from django.utils.encoding import force_str
from django.utils.timezone import is_naive, make_naive, now

from app.exceptions import AppServiceException
from app.services import BaseService


class Echo:
    """
    An object that implements just the write method (for StreamingHttpResponse).
    """

    def write(self, value: str) -> str:
        return value


class ExportModelAsCSVException(AppServiceException):
    """
    Raised if export fails.
    """


@dataclass
class ExportModelAsCSV(BaseService):
    """
    Stream admin queryset to CSV with optional date field + period filtering.
    """

    admin_view: Any
    request: Any
    queryset: QuerySet[Model]
    field_names: list[str] | None = None
    date_field: str | None = None
    period_days: int | None = None

    def act(self) -> StreamingHttpResponse:
        model = self.admin_view.model
        opts: Options = model._meta  # noqa: SLF001
        field_names = self.get_field_names(opts)
        queryset = self.get_filtered_queryset(model)

        return self.build_response(queryset, field_names, opts)

    def get_field_names(self, opts: Options) -> list[str]:
        return self.field_names or [field.name for field in opts.fields]

    def get_filtered_queryset(self, model: type[Model]) -> QuerySet[Model]:
        queryset = self.queryset
        if not queryset.exists():
            queryset = model.objects.all()  # type: ignore

        if self.date_field and self.period_days and self._model_has_field(model, self.date_field):
            filter_value = now() - timedelta(days=self.period_days)
            queryset = queryset.filter(**{f"{self.date_field}__gte": filter_value})

        return queryset.iterator()  # type: ignore

    def _model_has_field(self, model: type[Model], field_name: str) -> bool:
        try:
            model._meta.get_field(field_name)  # noqa: SLF001
            return True
        except LookupError:
            return False

    def build_response(
        self,
        queryset: Iterable[Model],
        field_names: list[str],
        opts: Options,
    ) -> StreamingHttpResponse:
        try:
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            response = StreamingHttpResponse(
                (writer.writerow(row) for row in self.generate_rows(queryset, field_names)),
                content_type="text/csv",
            )
            response["Content-Disposition"] = f'attachment; filename="{opts.model_name}.csv"'
            return response

        except Exception as e:  # noqa: BLE001
            raise ExportModelAsCSVException(f"CSV export failed: {e}")

    def generate_rows(self, queryset: Iterable[Model], field_names: list[str]) -> Iterable[list[str]]:
        yield field_names
        for obj in queryset:
            yield [self.format_value(getattr(obj, field)) for field in field_names]

    def format_value(self, value: Any) -> str:
        try:
            value = value() if callable(value) else value
            if hasattr(value, "isoformat"):
                return make_naive(value).isoformat() if is_naive(value) else value.isoformat()
            return force_str(value)

        except (TypeError, AttributeError, ValueError):
            return "ERROR"
