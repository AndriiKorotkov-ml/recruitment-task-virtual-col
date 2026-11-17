# Virtual columns in pandas + sales pipeline

Two parts:

- `solution.py` - `add_virtual_column(df, role, new_column)`
- `pipeline.py` - cleans `sales.csv` and writes revenue per region to `revenue_by_region.csv`

## Setup

You need Python 3.12+. I used [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Without uv, `pip install pandas pytest` in a virtualenv works too (pandas 3.x).

## Running

From the repo root (the pipeline reads `sales.csv` by relative path):

```bash
uv run python pipeline.py
```

It writes `revenue_by_region.csv` and prints how many rows each cleaning step changed.

## Tests

```bash
uv run pytest
```

- `test_virtual_column.py` - the provided tests, unchanged
- `test_solution.py` - my tests for `add_virtual_column`
- `test_pipeline.py` - tests for each cleaning step, plus one test that runs the whole pipeline on the real `sales.csv` and checks the numbers below

## Part 1: add_virtual_column

The function returns a copy of `df` with the new column, or an empty DataFrame if anything is wrong.

I don't use `eval` / `df.eval`. The role is first checked with a regex (`column (operator column)*`, spaces allowed), then split into tokens and evaluated by hand: the expression is split into terms on `+` and `-`, and `*` is applied inside each term. That gives the normal precedence, so `a + b * c` is `a + (b * c)`, and `a - b - c` is `(a - b) - c`.

### Ambiguities and assumptions

Things the task doesn't say, and what I chose:

- In the example in the task the function is called with `"total"` but the output shows `price_total`. I took that as a typo, the new column is named exactly `new_column`.
- "Any column label is incorrect" could mean every column in `df`. I only validate the labels the function actually uses: the ones in `role` and `new_column`. A badly named column that isn't used shouldn't block the calculation, and it's copied to the result unchanged.
- If `new_column` already exists in `df`, the result is an empty DataFrame. Overwriting silently would be the only place where bad input doesn't return empty, and it can destroy data (e.g. `"price * quantity"` into `"price"`).
- Columns used in `role` must be numeric. Text columns are rejected (`"ab" * 3` would quietly give `"ababab"`). Bool columns are rejected too, `True + True = 2` doesn't mean anything here.
- A single column with no operator (`"quantity"`) is valid and just copies the column.
- Column names are case-sensitive.
- Wrong argument types (not a DataFrame, `role` is `None`, etc.) return an empty DataFrame instead of raising.
- The input DataFrame is never modified, and dtypes are kept (int + int stays int64).

## Part 2: sales.csv

Revenue = `quantity * unit_price - discount`, computed with `add_virtual_column`.

The file is read with everything as strings first, because several columns have mixed formats and pandas would otherwise guess types wrong or turn things into NaN silently.

### Data problems

| # | Problem | Rows | Example | What I did |
|---|---|---|---|---|
| 1 | Header repeated in the middle of the file | 1 | line 753 | dropped |
| 2 | `TOTAL` row at the end | 1 | `TOTAL,,,37150,,65924.67,` | split off and used as a checksum (see below) |
| 3 | Column names with spaces and capitals | all columns | `"Quantity "`, `Unit Price` | strip, lowercase, spaces to `_` |
| 4 | Region spelled differently | 15 | `" South"`, `EAST`, `"west  "` | strip + title case, 5 regions left |
| 5 | Price with a decimal comma | 7 | `39,90` | comma to dot |
| 6 | Empty price | 4 | SO-10610, SO-11099, SO-11350, SO-11477 | filled with the price of the same product |
| 7 | Quantity with a space as thousands separator | 4 | `1 762` | parsed as 1762, kept, but suspicious (see below) |
| 8 | Negative quantity | 6 | `-2` to `-5` | kept, treated as returns |
| 9 | Empty discount | 963 | | set to 0 (the task says empty means no discount) |
| 10 | Fully duplicated rows | 5 | SO-10305 twice | dropped |

Checked and not a problem: no discount larger than the line amount (every discount is 5% or 10% of `quantity * unit_price`, rounded to cents), no zero prices, all dates are valid ISO dates (2026-01-02 to 2026-09-29), and every repeated order ID is a full copy of the row, not a different line of the same order.

### Ambiguities and assumptions

- The task says not to drop rows that can be fixed. The only rows I drop are the repeated header, the `TOTAL` row and the 5 exact duplicates. None of those is a real order line, and there's nothing to fix in a duplicate, keeping it would just count the order twice.
- Empty prices: each product has one price across the whole file, so I take it from the same product. SO-11477 confirms it, its discount 164.65 is 5% of 37 * 89.00, and 89.00 is the Keyboard price.
- Negative quantities I treat as returns and keep. They're small (-2 to -5) and the TOTAL quantity only matches with them in. It's still a guess: the IDs look like normal sales (`SO-`) and there's no original sale to match. Either way they only move total revenue by -913.
- 1762, 1745, 1371 and 1427 look like typos, every other quantity is between -5 and 40. I don't know the right values though, and TOTAL matches with them as they are, so I left them. Someone who owns the data should check these, they add a lot of revenue to North, South and Central.
- The task doesn't mention the TOTAL row. I use it as a checksum on quantity and discount, before removing duplicates (the total clearly includes them). Both sums match. If they didn't, the pipeline would print a warning and carry on, the check result is in the report anyway.
- `order_date` isn't needed for revenue, so I leave it as it is. I only checked that the dates are valid.
- Output: `region,revenue`, sorted by region, rounded to 2 decimals.

### Result

| region | revenue |
|---|---|
| Central | 515824.67 |
| East | 442219.91 |
| North | 665897.52 |
| South | 504036.04 |
| West | 442268.89 |
