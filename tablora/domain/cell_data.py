"""Cell-level data carried between IO, domain logic, and UI adapters."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CellData:
    """Represents one spreadsheet cell without binding to any UI widget.

    `value` is the editable cell payload. If `formula` is set, the formula
    string is preserved for XLSX/XLSM roundtrips. Style-related attributes are
    intentionally opaque so the IO layer can keep openpyxl references without
    making the domain package depend on openpyxl.
    """

    value: Any = None
    formula: str | None = None
    number_format: str | None = None
    style_id: Any = None
    readonly_style_ref: Any = None

    @classmethod
    def from_value(cls, value: Any) -> "CellData":
        """Create cell data and detect simple formula strings."""
        formula = value if isinstance(value, str) and value.startswith("=") else None
        return cls(value=value, formula=formula)

    def set_value(self, value: Any) -> None:
        """Update the editable value and keep formula metadata in sync."""
        self.value = value
        self.formula = value if isinstance(value, str) and value.startswith("=") else None
