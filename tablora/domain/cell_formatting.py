"""Cell formatting helpers for decimal numbers and dates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Literal


ValueFormatKind = Literal["decimal", "date"]
FormatSourceHint = Literal["auto", "de_decimal", "us_decimal", "de_date", "us_date", "iso_date", "month_en", "month_de"]
FormatTarget = Literal["de_decimal", "us_decimal", "de_date", "us_date", "iso_date", "month_en", "month_de"]
FormatStatus = Literal["changed", "unchanged", "ambiguous", "invalid", "empty"]

MONTHS_EN = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

MONTHS_DE = {
    "jan": 1,
    "januar": 1,
    "feb": 2,
    "februar": 2,
    "mär": 3,
    "märz": 3,
    "maer": 3,
    "maerz": 3,
    "mrz": 3,
    "apr": 4,
    "april": 4,
    "mai": 5,
    "jun": 6,
    "juni": 6,
    "jul": 7,
    "juli": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "okt": 10,
    "oktober": 10,
    "nov": 11,
    "november": 11,
    "dez": 12,
    "dezember": 12,
}

DECIMAL_SOURCE_OPTIONS: dict[ValueFormatKind, tuple[FormatSourceHint, ...]] = {
    "decimal": ("auto", "de_decimal", "us_decimal"),
    "date": ("auto", "de_date", "us_date", "iso_date", "month_en", "month_de"),
}
FORMAT_TARGET_OPTIONS: dict[ValueFormatKind, tuple[FormatTarget, ...]] = {
    "decimal": ("de_decimal", "us_decimal"),
    "date": ("de_date", "us_date", "iso_date", "month_en", "month_de"),
}

KIND_LABELS: dict[ValueFormatKind, str] = {
    "decimal": "Decimal numbers",
    "date": "Dates",
}
SOURCE_LABELS: dict[FormatSourceHint, str] = {
    "auto": "Auto",
    "de_decimal": "DEU decimal",
    "us_decimal": "US decimal",
    "de_date": "DEU numeric",
    "us_date": "US numeric",
    "iso_date": "ISO",
    "month_en": "Month name EN",
    "month_de": "Month name DE",
}
TARGET_LABELS: dict[FormatTarget, str] = {
    "de_decimal": "DEU decimal",
    "us_decimal": "US decimal",
    "de_date": "DEU",
    "us_date": "US",
    "iso_date": "ISO",
    "month_en": "DD MMM YYYY (EN)",
    "month_de": "DD MMM YYYY (DE)",
}


@dataclass(slots=True)
class FormatRequest:
    """User-selected formatting options."""

    kind: ValueFormatKind
    source_hint: FormatSourceHint
    target: FormatTarget


@dataclass(slots=True)
class FormatPreviewItem:
    """Preview row describing how one cell would be treated."""

    address: str
    original: str
    formatted: str
    status: FormatStatus
    note: str = ""


@dataclass(slots=True)
class FormatCellsResult:
    """Summary of formatting work for preview or application."""

    changed_count: int = 0
    unchanged_count: int = 0
    ambiguous_count: int = 0
    invalid_count: int = 0
    empty_count: int = 0
    metadata_only_count: int = 0
    text_changed_count: int = 0
    preview_items: list[FormatPreviewItem] = field(default_factory=list)

    @property
    def skipped_count(self) -> int:
        return self.ambiguous_count + self.invalid_count + self.empty_count

    def add_preview(self, item: FormatPreviewItem, *, limit: int) -> None:
        """Add a preview row when the limit has not been reached."""
        if len(self.preview_items) < limit:
            self.preview_items.append(item)

    def summary_message(self) -> str:
        """Return a compact user-facing result summary."""
        return (
            f"{self.changed_count} Zellen formatiert, "
            f"{self.skipped_count} übersprungen"
        )


@dataclass(slots=True)
class _DecimalValue:
    value: Decimal
    decimal_places: int


@dataclass(slots=True)
class _FormattingDecision:
    status: FormatStatus
    original_display: str
    formatted_display: str
    note: str = ""
    new_value: Any | None = None
    new_number_format: str | None = None
    metadata_only: bool = False
    text_changed: bool = False
    changed: bool = False


def source_options_for_kind(kind: ValueFormatKind) -> tuple[FormatSourceHint, ...]:
    """Return valid source options for the requested kind."""
    return DECIMAL_SOURCE_OPTIONS[kind]


def target_options_for_kind(kind: ValueFormatKind) -> tuple[FormatTarget, ...]:
    """Return valid target options for the requested kind."""
    return FORMAT_TARGET_OPTIONS[kind]


def format_cell_value(
    value: Any,
    *,
    number_format: str | None,
    request: FormatRequest,
) -> _FormattingDecision:
    """Return a formatting decision for one cell value."""
    if request.kind == "decimal":
        return _format_decimal_value(value, number_format=number_format, request=request)
    return _format_date_value(value, number_format=number_format, request=request)


def format_decimal_number_format(target: FormatTarget, decimal_places: int) -> str:
    """Return an Excel-style number format string for a decimal target."""
    locale_prefix = "[$-de-DE]" if target == "de_decimal" else "[$-en-US]"
    if decimal_places <= 0:
        return f"{locale_prefix}#,##0"
    return f"{locale_prefix}#,##0.{('0' * decimal_places)}"


def format_date_number_format(target: FormatTarget, has_time: bool, has_seconds: bool) -> str:
    """Return an Excel-style number format string for a date target."""
    if target == "de_date":
        base = "DD.MM.YYYY"
    elif target == "us_date":
        base = "MM/DD/YYYY"
    elif target == "iso_date":
        base = "YYYY-MM-DD"
    elif target == "month_en":
        base = "[$-en-US]DD MMM YYYY"
    else:
        base = "[$-de-DE]DD MMM YYYY"

    if has_seconds:
        return f"{base} HH:MM:SS"
    if has_time:
        return f"{base} HH:MM"
    return base


def _format_decimal_value(value: Any, *, number_format: str | None, request: FormatRequest) -> _FormattingDecision:
    original = "" if value is None else str(value)
    if value is None or (isinstance(value, str) and not value.strip()):
        return _FormattingDecision(status="empty", original_display=original, formatted_display=original, note="Leer")

    if isinstance(value, bool):
        return _FormattingDecision(status="invalid", original_display=original, formatted_display=original, note="Kein Dezimalwert")

    if isinstance(value, int):
        parsed = _DecimalValue(Decimal(value), 0)
        rendered = _render_decimal_text(parsed, request.target)
        new_number_format = format_decimal_number_format(request.target, 0)
        return _typed_numeric_decision(
            original=original,
            rendered=rendered,
            number_format=number_format,
            new_number_format=new_number_format,
        )

    if isinstance(value, float):
        parsed = _DecimalValue(Decimal(str(value)), _decimal_places_from_string(str(value)))
        rendered = _render_decimal_text(parsed, request.target)
        new_number_format = format_decimal_number_format(request.target, parsed.decimal_places)
        return _typed_numeric_decision(
            original=original,
            rendered=rendered,
            number_format=number_format,
            new_number_format=new_number_format,
        )

    if not isinstance(value, str):
        return _FormattingDecision(status="invalid", original_display=original, formatted_display=original, note="Kein Dezimalwert")

    parsed_string = _parse_decimal_string(value, request.source_hint)
    if parsed_string is None:
        return _FormattingDecision(status="invalid", original_display=original, formatted_display=original, note="Nicht erkannt")
    if parsed_string == "ambiguous":
        return _FormattingDecision(status="ambiguous", original_display=original, formatted_display=original, note="Mehrdeutig")

    rendered = _render_decimal_text(parsed_string, request.target)
    changed = rendered != value
    return _FormattingDecision(
        status="changed" if changed else "unchanged",
        original_display=original,
        formatted_display=rendered,
        new_value=rendered if changed else value,
        text_changed=changed,
        changed=changed,
    )


def _typed_numeric_decision(
    *,
    original: str,
    rendered: str,
    number_format: str | None,
    new_number_format: str,
) -> _FormattingDecision:
    changed = (number_format or "") != new_number_format
    return _FormattingDecision(
        status="changed" if changed else "unchanged",
        original_display=original,
        formatted_display=rendered,
        new_number_format=new_number_format if changed else number_format,
        metadata_only=changed,
        changed=changed,
    )


def _parse_decimal_string(text: str, source_hint: FormatSourceHint) -> _DecimalValue | Literal["ambiguous"] | None:
    stripped = text.strip()
    if not stripped:
        return None

    if source_hint == "de_decimal":
        return _parse_decimal_with_locale(stripped, decimal_separator=",", group_separator=".")
    if source_hint == "us_decimal":
        return _parse_decimal_with_locale(stripped, decimal_separator=".", group_separator=",")

    if re.fullmatch(r"[-+]?\d+", stripped):
        return _DecimalValue(Decimal(stripped), 0)

    # Values such as `0.526` or `0,526` are overwhelmingly used as decimals.
    # Treat them as fractional values instead of ambiguous thousands-grouped
    # integers when auto detection is active.
    if re.fullmatch(r"[-+]?0\.\d+", stripped):
        return _parse_decimal_with_locale(stripped, decimal_separator=".", group_separator=",")
    if re.fullmatch(r"[-+]?0,\d+", stripped):
        return _parse_decimal_with_locale(stripped, decimal_separator=",", group_separator=".")

    de_match = _parse_decimal_with_locale(stripped, decimal_separator=",", group_separator=".")
    us_match = _parse_decimal_with_locale(stripped, decimal_separator=".", group_separator=",")
    if de_match and us_match:
        return "ambiguous" if de_match.value != us_match.value else de_match
    return de_match or us_match


def _parse_decimal_with_locale(text: str, *, decimal_separator: str, group_separator: str) -> _DecimalValue | None:
    pattern = rf"[-+]?(?:\d{{1,3}}(?:\{group_separator}\d{{3}})+|\d+)(?:\{decimal_separator}\d+)?"
    if re.fullmatch(pattern, text) is None:
        return None

    normalized = text.replace(group_separator, "")
    if decimal_separator != ".":
        normalized = normalized.replace(decimal_separator, ".")
    decimal_places = 0
    if "." in normalized:
        decimal_places = len(normalized.rsplit(".", 1)[1])
    try:
        return _DecimalValue(Decimal(normalized), decimal_places)
    except InvalidOperation:
        return None


def _render_decimal_text(parsed: _DecimalValue, target: FormatTarget) -> str:
    rendered = f"{parsed.value:,.{parsed.decimal_places}f}"
    if target == "us_decimal":
        return rendered

    translation = rendered.replace(",", "\uFFFF").replace(".", ",").replace("\uFFFF", ".")
    return translation


def _format_date_value(value: Any, *, number_format: str | None, request: FormatRequest) -> _FormattingDecision:
    original = "" if value is None else str(value)
    if value is None or (isinstance(value, str) and not value.strip()):
        return _FormattingDecision(status="empty", original_display=original, formatted_display=original, note="Leer")

    if isinstance(value, datetime):
        rendered = _render_date_text(value, request.target)
        new_format = format_date_number_format(request.target, _has_time(value), _has_seconds(value))
        return _typed_date_decision(
            original=original,
            rendered=rendered,
            number_format=number_format,
            new_number_format=new_format,
        )

    if isinstance(value, date):
        current = datetime(value.year, value.month, value.day)
        rendered = _render_date_text(current, request.target)
        new_format = format_date_number_format(request.target, False, False)
        return _typed_date_decision(
            original=original,
            rendered=rendered,
            number_format=number_format,
            new_number_format=new_format,
        )

    if not isinstance(value, str):
        return _FormattingDecision(status="invalid", original_display=original, formatted_display=original, note="Kein Datum")

    parsed = _parse_date_string(value, request.source_hint)
    if parsed is None:
        return _FormattingDecision(status="invalid", original_display=original, formatted_display=original, note="Nicht erkannt")
    if parsed == "ambiguous":
        return _FormattingDecision(status="ambiguous", original_display=original, formatted_display=original, note="Mehrdeutig")

    rendered = _render_date_text(parsed, request.target)
    changed = rendered != value
    return _FormattingDecision(
        status="changed" if changed else "unchanged",
        original_display=original,
        formatted_display=rendered,
        new_value=rendered if changed else value,
        text_changed=changed,
        changed=changed,
    )


def _typed_date_decision(
    *,
    original: str,
    rendered: str,
    number_format: str | None,
    new_number_format: str,
) -> _FormattingDecision:
    changed = (number_format or "") != new_number_format
    return _FormattingDecision(
        status="changed" if changed else "unchanged",
        original_display=original,
        formatted_display=rendered,
        new_number_format=new_number_format if changed else number_format,
        metadata_only=changed,
        changed=changed,
    )


def _parse_date_string(text: str, source_hint: FormatSourceHint) -> datetime | Literal["ambiguous"] | None:
    stripped = text.strip()
    if not stripped:
        return None

    if source_hint == "iso_date":
        return _parse_iso_date(stripped)
    if source_hint == "month_en":
        return _parse_month_name_date(stripped, MONTHS_EN)
    if source_hint == "month_de":
        return _parse_month_name_date(stripped, MONTHS_DE)
    if source_hint == "de_date":
        return _parse_numeric_date(stripped, day_first=True)
    if source_hint == "us_date":
        return _parse_numeric_date(stripped, day_first=False)

    iso = _parse_iso_date(stripped)
    if iso is not None:
        return iso

    month_en = _parse_month_name_date(stripped, MONTHS_EN)
    if month_en is not None:
        return month_en

    month_de = _parse_month_name_date(stripped, MONTHS_DE)
    if month_de is not None:
        return month_de

    if "/" in stripped:
        maybe_de = _parse_numeric_date(stripped, day_first=True)
        maybe_us = _parse_numeric_date(stripped, day_first=False)
        if maybe_de is not None and maybe_us is not None and maybe_de != maybe_us:
            return "ambiguous"
        return maybe_de or maybe_us

    if "." in stripped:
        return _parse_numeric_date(stripped, day_first=True)

    if "-" in stripped:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?", stripped):
            return _parse_iso_date(stripped)
        return _parse_numeric_date(stripped, day_first=True)

    return None


def _parse_iso_date(text: str) -> datetime | None:
    candidate = text.replace("T", " ")
    patterns = ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")
    for pattern in patterns:
        try:
            return datetime.strptime(candidate, pattern)
        except ValueError:
            continue
    return None


def _parse_numeric_date(text: str, *, day_first: bool) -> datetime | None:
    separator = "." if "." in text else "/" if "/" in text else "-"
    date_part, time_part = _split_time(text)
    parts = date_part.split(separator)
    if len(parts) != 3:
        return None

    try:
        if day_first:
            day, month, year = (int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            month, day, year = (int(parts[0]), int(parts[1]), int(parts[2]))
        hour, minute, second = _parse_time_tuple(time_part)
        return datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None


def _parse_month_name_date(text: str, month_mapping: dict[str, int]) -> datetime | None:
    match = re.fullmatch(
        r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-zÄÖÜäöüß]{3,12})\.?\s+(?P<year>\d{4})(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?)?",
        text,
    )
    if match is None:
        return None

    month_key = match.group("month").casefold()
    month = month_mapping.get(month_key)
    if month is None:
        return None

    try:
        return datetime(
            int(match.group("year")),
            month,
            int(match.group("day")),
            int(match.group("hour") or 0),
            int(match.group("minute") or 0),
            int(match.group("second") or 0),
        )
    except ValueError:
        return None


def _render_date_text(value: datetime, target: FormatTarget) -> str:
    if target == "de_date":
        base = value.strftime("%d.%m.%Y")
    elif target == "us_date":
        base = value.strftime("%m/%d/%Y")
    elif target == "iso_date":
        base = value.strftime("%Y-%m-%d")
    elif target == "month_en":
        base = value.strftime("%d %b %Y")
    else:
        month_label = {
            1: "Jan",
            2: "Feb",
            3: "Mär",
            4: "Apr",
            5: "Mai",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Okt",
            11: "Nov",
            12: "Dez",
        }[value.month]
        base = f"{value.day:02d} {month_label} {value.year:04d}"

    if _has_seconds(value):
        return f"{base} {value:%H:%M:%S}"
    if _has_time(value):
        return f"{base} {value:%H:%M}"
    return base


def _split_time(text: str) -> tuple[str, str | None]:
    if " " not in text:
        return text, None
    date_part, time_part = text.split(" ", 1)
    return date_part, time_part.strip() or None


def _parse_time_tuple(time_part: str | None) -> tuple[int, int, int]:
    if not time_part:
        return 0, 0, 0
    pieces = time_part.split(":")
    if len(pieces) not in (2, 3):
        raise ValueError("Unsupported time")
    hour = int(pieces[0])
    minute = int(pieces[1])
    second = int(pieces[2]) if len(pieces) == 3 else 0
    return hour, minute, second


def _decimal_places_from_string(text: str) -> int:
    if "." not in text:
        return 0
    return len(text.rsplit(".", 1)[1])


def _has_time(value: datetime) -> bool:
    return any((value.hour, value.minute, value.second))


def _has_seconds(value: datetime) -> bool:
    return value.second != 0
