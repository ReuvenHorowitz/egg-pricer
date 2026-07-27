"""Pricing calculations for egg price review rows."""
from __future__ import annotations

from dataclasses import dataclass

from src.config import COST_CHANGE_TOLERANCE, ROUNDING_INCREMENT
from src.load_item_master import ItemMasterRow
from src.parse_martins_pdf import ParsedPdfRow


@dataclass
class PricedRow:
    item: ItemMasterRow
    parsed: ParsedPdfRow | None
    raw_list_price: float | None
    new_cost: float | None
    cost_change_dollar: float | None
    cost_change_pct: float | None
    current_price: float | None
    suggested_price: float | None
    action: str
    notes: str


def round_to_increment(value: float, increment: float = ROUNDING_INCREMENT) -> float:
    """Round a value to the nearest pricing increment."""
    return round(value / increment) * increment


def compute_price_row(item: ItemMasterRow, parsed_rows: dict[str, ParsedPdfRow]) -> PricedRow:
    """Compute pricing for one item master row."""
    parsed = parsed_rows.get(item.vendor_number)
    raw_list_price = parsed.raw_list_price if parsed else None

    if parsed is None:
        return PricedRow(
            item=item,
            parsed=None,
            raw_list_price=None,
            new_cost=None,
            cost_change_dollar=None,
            cost_change_pct=None,
            current_price=item.current_price,
            suggested_price=None,
            action="Missing - verify PDF",
            notes="Vendor item not found in PDF extract",
        )

    if raw_list_price is None:
        return PricedRow(
            item=item,
            parsed=parsed,
            raw_list_price=None,
            new_cost=None,
            cost_change_dollar=None,
            cost_change_pct=None,
            current_price=item.current_price,
            suggested_price=None,
            action="Parse error - manual review",
            notes="Matched PDF line but price could not be parsed",
        )

    new_cost = raw_list_price * item.cost_multiplier
    notes = ""

    if item.current_price and item.current_cost and item.current_price > 0:
        current_margin = (item.current_price - item.current_cost) / item.current_price
        suggested_price = new_cost / (1 - current_margin)
        notes = f"Margin preserved at {current_margin:.1%}"
    else:
        suggested_price = new_cost / (1 - item.target_margin)
        notes = f"Target margin applied at {item.target_margin:.1%}"

    suggested_price = round_to_increment(suggested_price)

    cost_change_dollar = None
    cost_change_pct = None
    if item.current_cost is not None:
        cost_change_dollar = new_cost - item.current_cost
        if item.current_cost > 0:
            cost_change_pct = cost_change_dollar / item.current_cost

    if item.current_cost is not None and abs(new_cost - item.current_cost) <= COST_CHANGE_TOLERANCE:
        action = "No cost change"
    elif item.current_cost is None:
        action = "Review - new cost"
    elif new_cost > item.current_cost:
        action = "Review - cost up"
    else:
        action = "Review - cost down"

    return PricedRow(
        item=item,
        parsed=parsed,
        raw_list_price=raw_list_price,
        new_cost=new_cost,
        cost_change_dollar=cost_change_dollar,
        cost_change_pct=cost_change_pct,
        current_price=item.current_price,
        suggested_price=suggested_price,
        action=action,
        notes=notes,
    )
