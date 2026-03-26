import pandas as pd
import math
from datetime import datetime, timedelta

# Labels that identify each metadata field (case-insensitive substring match)
_CLIENT_LABELS = ["client name", "client"]
_FISCAL_LABELS = ["fiscal year", "financial year", "year end", "fiscal end"]
_WORKPAPER_LABELS = ["workpaper"]
# The header row is identified by this value in column 0
_HEADER_MARKER = "account code"


def _safe_float(val):
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return None
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_str(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip()
    return s if s else None


def _excel_serial_to_date(serial: int) -> str:
    """Convert an Excel date serial number to YYYY-MM-DD string."""
    return (datetime(1899, 12, 30) + timedelta(days=serial)).strftime("%Y-%m-%d")


def _parse_date(val) -> str | None:
    """Return ISO date string from a pandas Timestamp, Excel serial int, or date string."""
    if val is None:
        return None
    # pandas Timestamp / datetime
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    # Excel serial stored as int or float
    if isinstance(val, (int, float)) and not math.isnan(float(val)):
        num = int(val)
        if 1000 < num < 100000:          # plausible Excel date range
            return _excel_serial_to_date(num)
    # Plain string — return as-is after stripping
    s = _safe_str(val)
    return s


def _matches(label_val, targets: list[str]) -> bool:
    if label_val is None:
        return False
    norm = str(label_val).strip().lower()
    return any(t in norm for t in targets)


def parse_tb_formatted(df):
    """
    Parses the first sheet of a Trial Balance Excel file.

    Scans rows dynamically to find metadata labels (case-insensitive),
    then finds the data header row by looking for 'Account Code'.
    Handles Excel serial date numbers stored as integers.
    """
    client_name = None
    fiscal_year_end = None
    workpaper = None
    header_row_idx = None

    for i in range(min(20, len(df))):       # metadata is always near the top
        label = df.iloc[i, 0]
        value = df.iloc[i, 1] if df.shape[1] > 1 else None

        if _matches(label, _CLIENT_LABELS) and client_name is None:
            client_name = _safe_str(value)

        elif _matches(label, _FISCAL_LABELS) and fiscal_year_end is None:
            fiscal_year_end = _parse_date(value)

        elif _matches(label, _WORKPAPER_LABELS) and workpaper is None:
            workpaper = _safe_str(value)

        elif _matches(label, [_HEADER_MARKER]):
            header_row_idx = i
            break

    # If header not found in first pass, scan further
    if header_row_idx is None:
        for i in range(len(df)):
            if _matches(df.iloc[i, 0], [_HEADER_MARKER]):
                header_row_idx = i
                break

    data_start = (header_row_idx + 1) if header_row_idx is not None else 0

    line_items = []
    for i in range(data_start, len(df)):
        row = df.iloc[i]
        code = _safe_str(row.iloc[0])
        if code is None:
            continue
        # Skip rows that look like another header/label
        if _matches(code, [_HEADER_MARKER]):
            continue
        line_items.append(
            {
                "account_code": code,
                "account_description": _safe_str(row.iloc[1]) or "",
                "amount": _safe_float(row.iloc[2]),
            }
        )

    return {
        "client_name": client_name,
        "workpaper": workpaper,
        "fiscal_year_end": fiscal_year_end,
        "line_items": line_items,
    }


def parse_trial_balance_excel(file_path: str) -> dict:
    """
    Main entry point. Reads the first sheet and returns metadata + line items.
    """
    xl = pd.ExcelFile(file_path)
    df = xl.parse(xl.sheet_names[0], header=None)
    return parse_tb_formatted(df)
