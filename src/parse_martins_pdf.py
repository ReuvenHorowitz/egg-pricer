"""Parse Martin's Quality Eggs price list PDFs."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

LINE_PATTERN = re.compile(r"^(\S+)\s+(.+?)\s+\.{2,}\s*(\d*\.\d+)\s*$")
PRICE_DATE_PATTERN = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4})")


@dataclass(frozen=True)
class ParsedPdfRow:
    vendor_number: str
    raw_list_price: float | None
    description_from_pdf: str
    source_page: int
    source_line: str
    matched: bool


@dataclass(frozen=True)
class PdfMetadata:
    customer_code: str | None
    price_date: str | None
    filename: str


def _normalize_price(price_text: str) -> float:
    return float(price_text)


def parse_martins_pdf(pdf_path: Path, tracked_vendor_numbers: list[str]) -> tuple[dict[str, ParsedPdfRow], PdfMetadata]:
    """Extract tracked vendor rows from a Martin's price list PDF."""
    tracked = {vendor.upper() for vendor in tracked_vendor_numbers}
    results: dict[str, ParsedPdfRow] = {}
    customer_code: str | None = None
    price_date: str | None = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue

                if customer_code is None and stripped.startswith("ALFOOI0"):
                    customer_code = "ALFOOI0"

                if price_date is None:
                    date_match = PRICE_DATE_PATTERN.search(stripped)
                    if date_match:
                        price_date = date_match.group(1)

                match = LINE_PATTERN.match(stripped)
                if not match:
                    continue

                vendor_number = match.group(1).upper()
                if vendor_number not in tracked:
                    continue

                description = match.group(2).strip()
                try:
                    raw_price = _normalize_price(match.group(3))
                except ValueError:
                    raw_price = None

                results[vendor_number] = ParsedPdfRow(
                    vendor_number=vendor_number,
                    raw_list_price=raw_price,
                    description_from_pdf=description,
                    source_page=page_number,
                    source_line=stripped,
                    matched=raw_price is not None,
                )

    for vendor in tracked_vendor_numbers:
        vendor_key = vendor.upper()
        if vendor_key not in results:
            print(f"WARNING: Vendor item {vendor_key} not found in PDF: {pdf_path.name}")
            results[vendor_key] = ParsedPdfRow(
                vendor_number=vendor_key,
                raw_list_price=None,
                description_from_pdf="",
                source_page=0,
                source_line="",
                matched=False,
            )

    metadata = PdfMetadata(
        customer_code=customer_code,
        price_date=price_date,
        filename=pdf_path.name,
    )
    return results, metadata
