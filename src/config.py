"""Project configuration and path helpers."""
from __future__ import annotations

from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PDF_DIR = PROJECT_ROOT / "input" / "current_pdf"
ITEM_MASTER_PATH = PROJECT_ROOT / "data" / "item_master.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"
PRICE_HISTORY_PATH = PROJECT_ROOT / "price_history.csv"

TRACKED_VENDOR_NUMBERS = ["6ELE15", "2XWL", "3WFP", "7HC2"]
ROUNDING_INCREMENT = 0.05
COST_CHANGE_TOLERANCE = 0.001

CURRENCY_FORMAT = "$#,##0.00"
PERCENT_FORMAT = "0.0%"

YELLOW_FILL = "FFFFF2CC"
RED_FILL = "FFFFCCCC"

ITEM_MASTER_COLUMNS = [
    "item_number",
    "description",
    "vendor_number",
    "pack_size",
    "cost_multiplier",
    "current_cost",
    "current_price",
    "target_margin",
    "rounding_rule",
]


class ConfigError(Exception):
    """Raised when required project inputs are missing or invalid."""


def get_latest_pdf() -> Path:
    """Return the newest PDF in the input directory."""
    if not INPUT_PDF_DIR.exists():
        raise ConfigError(f"Input directory not found: {INPUT_PDF_DIR}")

    pdfs = sorted(INPUT_PDF_DIR.glob("*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
    pdfs.extend(
        sorted(INPUT_PDF_DIR.glob("*.PDF"), key=lambda path: path.stat().st_mtime, reverse=True)
    )
    pdfs = sorted({path.resolve(): path for path in pdfs}.values(), key=lambda p: p.stat().st_mtime, reverse=True)

    if not pdfs:
        raise ConfigError(f"No PDF found in {INPUT_PDF_DIR}")

    return pdfs[0]


def build_output_path(run_date: date | None = None) -> Path:
    """Build a non-colliding output workbook path for the run date."""
    run_date = run_date or date.today()
    base_name = f"Martins Egg Price Review {run_date.isoformat()}.xlsx"
    candidate = OUTPUT_DIR / base_name
    if not candidate.exists():
        return candidate

    suffix = 2
    while True:
        candidate = OUTPUT_DIR / f"Martins Egg Price Review {run_date.isoformat()}_{suffix}.xlsx"
        if not candidate.exists():
            return candidate
        suffix += 1
