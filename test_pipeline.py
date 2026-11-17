import pandas as pd
import pytest

from pipeline import (
    add_revenue,
    check_against_total,
    normalize_column_names,
    normalize_regions,
    parse_numbers,
    remove_duplicates,
    restore_prices,
    run_pipeline,
)


def test_normalize_column_names():
    df = pd.DataFrame({"QuaNtity ": [1], " unit Price ": [2]})

    expected = pd.DataFrame({"quantity": [1], "unit_price": [2]})
    df = normalize_column_names(df)

    pd.testing.assert_frame_equal(df, expected)


def test_normalize_regions():
    df = pd.DataFrame({"region": ["WEST", " north ", "eAst ", "South"]})
    expected = pd.DataFrame({"region": ["West", "North", "East", "South"]})

    df, changed = normalize_regions(df)
    assert changed == 3
    pd.testing.assert_frame_equal(df, expected)


def test_parse_numbers_handles_comma_space_and_empty():
    df = pd.DataFrame(
        {
            "quantity": ["1 762", "3"],
            "unit_price": ["39,90", ""],
            "discount": ["", "5.5"],
        }
    )

    result, counts = parse_numbers(df)

    assert result["quantity"].tolist() == [1762, 3]
    assert result["unit_price"].iloc[0] == 39.9
    assert pd.isna(result["unit_price"].iloc[1])
    assert counts == {
        "comma_prices": 1,
        "space_quantity": 1,
        "empty_discounts": 1,
    }


def test_add_revenue_raises_on_text_column():
    df = pd.DataFrame({"quantity": ["3"], "unit_price": [10.0], "discount": [5.0]})
    with pytest.raises(ValueError):
        add_revenue(df)


def test_add_revenue_computes_quantity_times_price_minus_discount():
    df = pd.DataFrame({"quantity": [3], "unit_price": [10.0], "discount": [5.0]})

    result = add_revenue(df)

    assert result["revenue"].tolist() == [25.0]


def test_restore_prices_uses_price_of_same_product():
    df = pd.DataFrame(
        {"product": ["Mouse", "Keyboard", "Mouse"], "unit_price": [29.5, 89.0, None]}
    )

    result, restored = restore_prices(df)

    assert result["unit_price"].tolist() == [29.5, 89.0, 29.5]
    assert restored == 1


def test_remove_duplicates_keeps_same_id_with_different_values():
    df = pd.DataFrame({"order_id": ["SO-1", "SO-1", "SO-1"], "quantity": [5, 5, 8]})
    result, removed = remove_duplicates(df)

    assert len(result) == 2
    assert removed == 1


def test_check_against_total():
    df = pd.DataFrame({"quantity": [2, 3], "discount": [1.5, 0.0]})
    total_ok = pd.DataFrame({"quantity": [5], "discount": [1.5]})
    total_bad = pd.DataFrame({"quantity": [6], "discount": [1.5]})

    assert check_against_total(df, total_ok) is True
    assert check_against_total(df, total_bad) is False


def test_run_pipeline_on_real_sales_file():
    result, report = run_pipeline("sales.csv")

    assert report == {
        "repeated_headers": 1,
        "changed_regions": 15,
        "comma_prices": 7,
        "space_quantity": 4,
        "empty_discounts": 963,
        "total_check_passed": True,
        "filled_discounts": 963,
        "restored_prices": 4,
        "removed_duplicates": 5,
    }
    assert result["region"].tolist() == ["Central", "East", "North", "South", "West"]
    assert result["revenue"].isna().sum() == 0
    assert result.loc[result["region"] == "Central", "revenue"].iloc[0] == 515824.67
