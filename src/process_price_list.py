"""Orchestrate PDF parsing, pricing, history logging, and report generation."""
from __future__ import annotations

import csv
import os
import tempfile
from datetime import datetime
from pathlib import Path

from src.build_excel_report import build_excel_report
from src.config import (
    ConfigError,
    ITEM_MASTER_PATH,
    OUTPUT_DIR,
    PRICE_HISTORY_PATH,
    TRACKED_VENDOR_NUMBERS,
    build_output_path,
    get_latest_pdf,
)
from src.load_item_master import ItemMasterError, load_item_master
from src.parse_martins_pdf import parse_martins_pdf
from src.price_math import PricedRow, compute_price_row

HISTORY_HEADERS = [
    "run_timestamp",
    "run_date",
    "pdf_filename",
    "item_number",
    "description",
    "vendor_number",
    "raw_list_price",
    "cost_multiplier",
    "new_cost",
    "current_cost",
    "current_price",
    "suggested_price",
    "cost_change_dollar",
    "cost_change_pct",
    "action",
]


def append_price_history(priced_rows: list[PricedRow], pdf_filename: str) -> Path:
    """Append one history row per item without overwriting prior runs."""
    run_time = datetime.now()
    write_header = not PRICE_HISTORY_PATH.exists() or PRICE_HISTORY_PATH.stat().st_size == 0
    if not write_header:
        with PRICE_HISTORY_PATH.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            existing_headers = reader.fieldnames or []
            existing_rows = list(reader)

        if "description" not in existing_headers:
            with tempfile.NamedTemporaryFile(
                "w",
                newline="",
                encoding="utf-8",
                dir=PRICE_HISTORY_PATH.parent,
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                writer = csv.DictWriter(temporary, fieldnames=HISTORY_HEADERS)
                writer.writeheader()
                writer.writerows(existing_rows)
            os.replace(temporary_path, PRICE_HISTORY_PATH)

    with PRICE_HISTORY_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_HEADERS)
        if write_header:
            writer.writeheader()

        for priced in priced_rows:
            writer.writerow(
                {
                    "run_timestamp": run_time.isoformat(timespec="seconds"),
                    "run_date": run_time.date().isoformat(),
                    "pdf_filename": pdf_filename,
                    "item_number": priced.item.item_number,
                    "description": priced.item.description,
                    "vendor_number": priced.item.vendor_number,
                    "raw_list_price": priced.raw_list_price,
                    "cost_multiplier": priced.item.cost_multiplier,
                    "new_cost": priced.new_cost,
                    "current_cost": priced.item.current_cost,
                    "current_price": priced.current_price,
                    "suggested_price": priced.suggested_price,
                    "cost_change_dollar": priced.cost_change_dollar,
                    "cost_change_pct": priced.cost_change_pct,
                    "action": priced.action,
                }
            )

    return PRICE_HISTORY_PATH


def _print_summary(priced_rows: list[PricedRow], report_path: Path, history_path: Path) -> None:
    print("\nEgg Price Review Summary")
    headers = ("Item Code", "Description", "Vendor", "Raw Price", "New Cost", "Suggested", "Action")
    rows = []
    for priced in priced_rows:
        raw_price = f"{priced.raw_list_price:.4f}" if priced.raw_list_price is not None else "MISSING"
        new_cost = f"${priced.new_cost:.2f}" if priced.new_cost is not None else "N/A"
        suggested = f"${priced.suggested_price:.2f}" if priced.suggested_price is not None else "N/A"
        rows.append(
            (
                priced.item.item_number,
                priced.item.description,
                priced.item.vendor_number,
                raw_price,
                new_cost,
                suggested,
                priced.action,
            )
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    alignments = ("<", "<", "<", ">", ">", ">", "<")
    table_width = sum(widths) + 2 * (len(headers) - 1)
    print("-" * table_width)
    print("  ".join(f"{value:{alignments[index]}{widths[index]}}" for index, value in enumerate(headers)))
    print("-" * table_width)
    for row in rows:
        print("  ".join(f"{value:{alignments[index]}{widths[index]}}" for index, value in enumerate(row)))
    print("-" * table_width)
    print(f"Report:  {report_path}")
    print(f"History: {history_path}")


def main() -> int:
    """Run the full price review workflow."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ITEM_MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)

        pdf_path = get_latest_pdf()
        added_date = datetime.fromtimestamp(pdf_path.stat().st_ctime).date().isoformat()
        print(f"Reading input file: {pdf_path} (added to input folder: {added_date})")
        items = load_item_master()
        parsed_rows, pdf_metadata = parse_martins_pdf(pdf_path, TRACKED_VENDOR_NUMBERS)
        priced_rows = [compute_price_row(item, parsed_rows) for item in items]

        history_path = append_price_history(priced_rows, pdf_path.name)
        report_path = build_output_path()
        build_excel_report(priced_rows, parsed_rows, pdf_metadata, pdf_path, report_path)
        _print_summary(priced_rows, report_path, history_path)
        return 0
    except (ConfigError, ItemMasterError) as exc:
        print(f"ERROR: {exc}")
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
