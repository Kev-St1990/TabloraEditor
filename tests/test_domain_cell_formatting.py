"""Tests for decimal and date formatting helpers."""

from datetime import datetime
import unittest

from tablora.domain import FormatRequest
from tablora.domain.cell_formatting import format_cell_value


class CellFormattingTests(unittest.TestCase):
    """Verify parsing, ambiguity handling, and rendering rules."""

    def test_decimal_string_converts_between_de_and_us(self) -> None:
        decision = format_cell_value(
            "1.234,56",
            number_format=None,
            request=FormatRequest(kind="decimal", source_hint="de_decimal", target="us_decimal"),
        )

        self.assertEqual(decision.status, "changed")
        self.assertEqual(decision.formatted_display, "1,234.56")
        self.assertEqual(decision.new_value, "1,234.56")
        self.assertTrue(decision.text_changed)

    def test_decimal_numeric_value_prefers_number_format_change(self) -> None:
        decision = format_cell_value(
            1234.5,
            number_format="General",
            request=FormatRequest(kind="decimal", source_hint="auto", target="de_decimal"),
        )

        self.assertEqual(decision.status, "changed")
        self.assertTrue(decision.metadata_only)
        self.assertEqual(decision.formatted_display, "1.234,5")
        self.assertEqual(decision.new_number_format, "[$-de-DE]#,##0.0")

    def test_auto_decimal_treats_leading_zero_fraction_as_decimal(self) -> None:
        decision = format_cell_value(
            "0.526",
            number_format=None,
            request=FormatRequest(kind="decimal", source_hint="auto", target="de_decimal"),
        )

        self.assertEqual(decision.status, "changed")
        self.assertEqual(decision.formatted_display, "0,526")
        self.assertEqual(decision.new_value, "0,526")

    def test_auto_date_recognizes_english_and_german_months(self) -> None:
        english = format_cell_value(
            "23 Jan 2024",
            number_format=None,
            request=FormatRequest(kind="date", source_hint="auto", target="de_date"),
        )
        german = format_cell_value(
            "01 Mär 2024",
            number_format=None,
            request=FormatRequest(kind="date", source_hint="auto", target="us_date"),
        )

        self.assertEqual(english.formatted_display, "23.01.2024")
        self.assertEqual(german.formatted_display, "03/01/2024")

    def test_auto_date_marks_ambiguous_slash_dates(self) -> None:
        decision = format_cell_value(
            "01/02/2024",
            number_format=None,
            request=FormatRequest(kind="date", source_hint="auto", target="iso_date"),
        )

        self.assertEqual(decision.status, "ambiguous")
        self.assertEqual(decision.note, "Mehrdeutig")

    def test_auto_date_accepts_unambiguous_day_first_date(self) -> None:
        decision = format_cell_value(
            "13/02/2024",
            number_format=None,
            request=FormatRequest(kind="date", source_hint="auto", target="iso_date"),
        )

        self.assertEqual(decision.status, "changed")
        self.assertEqual(decision.formatted_display, "2024-02-13")

    def test_datetime_value_preserves_time_in_preview_and_number_format(self) -> None:
        decision = format_cell_value(
            datetime(2024, 6, 4, 15, 45),
            number_format="YYYY-MM-DD HH:MM",
            request=FormatRequest(kind="date", source_hint="auto", target="month_en"),
        )

        self.assertEqual(decision.status, "changed")
        self.assertTrue(decision.metadata_only)
        self.assertEqual(decision.formatted_display, "04 Jun 2024 15:45")
        self.assertEqual(decision.new_number_format, "[$-en-US]DD MMM YYYY HH:MM")


if __name__ == "__main__":
    unittest.main()
