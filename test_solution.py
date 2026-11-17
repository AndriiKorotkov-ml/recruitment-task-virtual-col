import pandas as pd
import pytest

from solution import add_virtual_column


def test_multiplication_before_addition_and_subtraction():
    df = pd.DataFrame({"a": [2], "b": [3], "c": [4], "d": [1]})

    df_exp = df.assign(result=[13])

    result = add_virtual_column(df, "a + b * c - d", "result")

    pd.testing.assert_frame_equal(result, df_exp)


def test_subtraction_from_left_to_right():
    df = pd.DataFrame({"a": [10], "b": [3], "c": [4], "d": [1]})

    expected = df.assign(result=[2])

    result = add_virtual_column(df, "a - b - c - d", "result")
    pd.testing.assert_frame_equal(expected, result)


def test_single_column():
    df = pd.DataFrame({"a": [10], "b": [3], "c": [4], "d": [1]})

    expected = df.assign(result=[10])

    result = add_virtual_column(df, "a", "result")
    pd.testing.assert_frame_equal(expected, result)


def test_fraction_operations():
    df = pd.DataFrame({"a": [2.5], "b": [3.0], "c": [4.0], "d": [1.5]})

    expected = df.assign(result=[11.5])

    result = add_virtual_column(df, "a + b + c * d", "result")

    pd.testing.assert_frame_equal(expected, result)


@pytest.mark.parametrize(
    "role",
    [
        "+a",
        "a +",
        "a + + b",
        "a ** b",
        "a b",
        "a/b",
        "a + 1",
        "",
        "    ",
        "(a+b)",
        None,
    ],
)
def test_invalid_role_returns_empty_df(role):
    df = pd.DataFrame({"a": [1], "b": [2]})
    result = add_virtual_column(df, role, "result")
    assert result.empty


def test_text_column_returns_empty_df():
    df = pd.DataFrame({"a": ["ab"], "b": [3]})

    result = add_virtual_column(df, "a*b", "result")

    assert result.empty


def test_bool_column_returns_empty_df():

    df = pd.DataFrame({"a": [True], "b": [23]})

    result = add_virtual_column(df, "a + b", "result")

    assert result.empty


def test_existing_new_column_returns_empty_df():
    df = pd.DataFrame({"a": [1], "b": [2]})

    result = add_virtual_column(df, "a+b", "a")

    assert result.empty


@pytest.mark.parametrize(
    "new_column",
    [
        "label3",
        "label$#",
        " label ",
        "lab el",
        "lab-el",
        "",
        " ",
        None,
    ],
)
def test_invalid_new_column_returns_empty_df(new_column):
    df = pd.DataFrame({"a": [1], "b": [2]})

    result = add_virtual_column(df, "a + b", new_column)

    assert result.empty


def test_input_df_is_not_modified():
    df = pd.DataFrame({"a": [1], "b": [2]})

    original = df.copy()
    add_virtual_column(df, "a+b", "result")
    pd.testing.assert_frame_equal(df, original)


@pytest.mark.parametrize("df", [None, {"a": [1], "b": [2]}])
def test_not_a_dataframe_returns_empty_df(df):
    result = add_virtual_column(df, "a+b", "result")

    assert result.empty
