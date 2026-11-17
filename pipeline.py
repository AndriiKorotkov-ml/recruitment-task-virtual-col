import math

import pandas as pd

from solution import add_virtual_column


def read_raw(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def remove_repeated_headers(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    mask = (df == df.columns).all(axis=1)

    return df[~mask], int(mask.sum())


def split_total_row(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    is_total = df["Order ID"] == "TOTAL"
    return df[~is_total], df[is_total]


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    df_clean.columns = (
        df_clean.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    )
    return df_clean


def normalize_regions(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df_clean = df.copy()
    old = df_clean["region"]
    df_clean["region"] = df_clean["region"].str.strip().str.title()
    changed = int((old != df_clean["region"]).sum())
    return df_clean, changed


def parse_numbers(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    comma_num = int((df["unit_price"].str.contains(",", regex=False)).sum())
    space_num = int((df["quantity"].str.contains(" ", regex=False)).sum())
    blank_val = int((df["discount"].str.fullmatch("")).sum())
    df_clean = df.copy()

    df_clean["unit_price"] = pd.to_numeric(
        df_clean["unit_price"].str.replace(",", ".", regex=False).replace("", None)
    )
    df_clean["quantity"] = pd.to_numeric(
        df_clean["quantity"].str.replace(" ", "", regex=False)
    )
    df_clean["discount"] = pd.to_numeric(
        df_clean["discount"].replace("", None, regex=False)
    )
    return df_clean, {
        "comma_prices": comma_num,
        "space_quantity": space_num,
        "empty_discounts": blank_val,
    }


def check_against_total(df: pd.DataFrame, total: pd.DataFrame) -> bool:
    exp_quantity = total["quantity"].iloc[0]
    exp_disc = total["discount"].iloc[0]
    actual_quantity = df["quantity"].sum(skipna=True)
    actual_disc = df["discount"].sum(skipna=True)
    match = math.isclose(exp_quantity, actual_quantity) and math.isclose(
        exp_disc, actual_disc
    )

    if not match:
        print("Warning: the actual sum is not equal to expected.")
    return match


def fill_discounts(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df_clean = df.copy()
    filled = int(df_clean["discount"].isna().sum())
    df_clean["discount"] = df_clean["discount"].fillna(0)
    return df_clean, filled


def restore_prices(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df_clean = df.copy()
    restored = int(df_clean["unit_price"].isna().sum())
    product_price = df_clean.groupby("product")["unit_price"].transform("first")
    df_clean["unit_price"] = df_clean["unit_price"].fillna(product_price)

    return df_clean, restored


def remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df_clean = df.copy()
    dropped = int(df_clean.duplicated().sum())

    df_clean = df_clean.drop_duplicates()

    return df_clean, dropped


def add_revenue(df: pd.DataFrame) -> pd.DataFrame:

    result = add_virtual_column(df, "quantity * unit_price - discount", "revenue")

    if result.empty:
        raise ValueError("Could not compute revenue")
    return result


def revenue_by_region(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("region", as_index=False)["revenue"].sum().round(2)


def main() -> None:
    report = {}

    df = read_raw("./sales.csv")
    df, report["repeated_headers"] = remove_repeated_headers(df)
    df, total = split_total_row(df)
    df = normalize_column_names(df)
    df, report["changed_regions"] = normalize_regions(df)
    df, number_counts = parse_numbers(df)
    report.update(number_counts)
    total = normalize_column_names(total)
    total, _ = parse_numbers(total)
    report["total_check_passed"] = check_against_total(df, total)
    df, report["filled_discounts"] = fill_discounts(df)
    df, report["restored_prices"] = restore_prices(df)
    df, report["removed_duplicates"] = remove_duplicates(df)
    df = add_revenue(df)
    revenue_by_reg = revenue_by_region(df)
    revenue_by_reg.to_csv("revenue_by_region.csv", index=False)

    for name, value in report.items():
        print(f"{name}:{value}")


if __name__ == "__main__":
    main()
