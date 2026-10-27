# Egg Price Checker

Weekly automation for Martin's Quality Eggs price lists. Extracts four tracked vendor items, applies multiplier and margin pricing logic, appends run history, and creates a review workbook.

## Tracked vendor items

- `6ELE15`
- `2XWL`
- `3WFP`
- `7HC2`

## Setup

```bash
pip install -r requirements.txt
```

Create `data/item_master.xlsx` from `data/item_master.template.csv` (open in Excel and Save As `.xlsx`) or copy a blank workbook with these columns:

`item_number`, `description`, `vendor_number`, `pack_size`, `cost_multiplier`, `current_cost`, `current_price`, `target_margin`, `rounding_rule`

Fill in your Business Central item numbers, costs, prices, and multipliers.

## Usage

1. Drop the latest Martin's PDF directly into `input/`. The program selects the PDF with the newest file creation date (the date it was added to the folder on Windows) and prints its path and added date when it runs.
2. **Close** `data/item_master.xlsx` if it is open in Excel
3. Run from the project folder:

```powershell
cd "C:\Users\rhorowitz\OneDrive - A&L Foods\Desktop\Code\egg pricer"
python run.py
```

On Windows PowerShell, use `python run.py` (not `run.py` alone).

## Outputs

- `output/Martins Egg Price Review YYYY-MM-DD.xlsx`
  - **Price Change Review** — main report with current vs new cost and suggested price
  - **Raw Extract** — PDF audit rows
  - **Settings** — run metadata and formulas
- `price_history.csv` — append-only history of every run (never overwritten)

## Pricing logic

```text
new_cost = raw_list_price * cost_multiplier
```

If `current_price` and `current_cost` exist:

```text
current_margin = (current_price - current_cost) / current_price
suggested_price = new_cost / (1 - current_margin)
```

Otherwise:

```text
suggested_price = new_cost / (1 - target_margin)
```

Suggested prices are always rounded **up** to the next `$0.05` (never rounded down).

## Notes

- v1 is review-only and does **not** update Business Central
- Missing PDF items are highlighted in red and logged to the console
- Changed costs are highlighted in yellow on the review sheet
- Raw PDF list prices are kept separate from calculated case costs
- **Git:** PDFs, `item_master.xlsx`, output workbooks, and `price_history.csv` are gitignored and stay on your machine only
