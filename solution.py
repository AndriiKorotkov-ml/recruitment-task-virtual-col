import re

import pandas as pd

LABEL_PATTERN = "[A-Za-z_]+"
OPERATOR_PATTERN = "[-+*]"
ROLE_PATTERN = rf"\s*{LABEL_PATTERN}(\s*{OPERATOR_PATTERN}\s*{LABEL_PATTERN})*\s*"


def is_valid_label(label: str) -> bool:
    if not isinstance(label, str):
        return False
    return bool(re.fullmatch(LABEL_PATTERN, label))


def parse_role(role: str) -> list[str] | None:
    if not isinstance(role, str):
        return None
    if not re.fullmatch(ROLE_PATTERN, role):
        return None
    return re.findall(rf"{LABEL_PATTERN}|{OPERATOR_PATTERN}", role)


def add_term(result: pd.Series | None, term: pd.Series, sign: str) -> pd.Series:
    if result is None:
        if sign == "+":
            return term
        elif sign == "-":
            return -term
    else:
        if sign == "+":
            return result + term
        elif sign == "-":
            return result - term


def evaluate(df: pd.DataFrame, tokens: list[str]) -> pd.Series:
    result = None
    sign = "+"
    term = df[tokens[0]]

    for i in range(1, len(tokens), 2):
        operator = tokens[i]
        column = df[tokens[i + 1]]
        if operator == "*":
            term = term * column
        else:
            result = add_term(result, term, sign)
            sign = operator
            term = column
    return add_term(result, term, sign)


def add_virtual_column(df: pd.DataFrame, role: str, new_column: str) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    if not is_valid_label(new_column) or new_column in df.columns:
        return pd.DataFrame()
    tokens = parse_role(role)

    if tokens is None:
        return pd.DataFrame()

    for label in tokens[::2]:
        if (
            label not in df.columns
            or not pd.api.types.is_numeric_dtype(df[label])
            or pd.api.types.is_bool_dtype(df[label])
        ):
            return pd.DataFrame()
    result = df.copy()

    result[new_column] = evaluate(df, tokens)
    return result
