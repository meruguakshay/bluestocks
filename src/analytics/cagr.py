import pandas as pd


def calculate_cagr(end_val, start_val, n):
    """
    Computes CAGR for a given period of n years.
    Formula: ((end_val / start_val) ** (1 / n) - 1) * 100

    Handles 6 edge cases:
    1. Less than n years of data (INSUFFICIENT)
    2. Zero base value (ZERO_BASE)
    3. Positive start, negative end (DECLINE_TO_LOSS)
    4. Negative start, positive end (TURNAROUND)
    5. Negative start, negative end (BOTH_NEGATIVE)
    6. Positive start, positive end (Normal calculation)

    Returns:
        (cagr_value, flag_label)
    """
    # 1. Check for missing values / insufficient data
    if start_val is None or pd.isna(start_val) or end_val is None or pd.isna(end_val):
        return None, "INSUFFICIENT"

    # Cast to float for math operations
    try:
        start = float(start_val)
        end = float(end_val)
    except (ValueError, TypeError):
        return None, "INSUFFICIENT"

    # 2. Zero base
    if start == 0.0:
        return None, "ZERO_BASE"

    # 3. Positive start, negative end (or zero end - wait, zero end can be computed normally as -100%)
    if start > 0.0 and end < 0.0:
        return None, "DECLINE_TO_LOSS"

    # 4. Negative start, positive end (or zero end)
    if start < 0.0 and end >= 0.0:
        return None, "TURNAROUND"

    # 5. Negative start, negative end
    if start < 0.0 and end < 0.0:
        return None, "BOTH_NEGATIVE"

    # 6. Normal positive start, positive/zero end
    try:
        cagr = ((end / start) ** (1.0 / n) - 1.0) * 100.0
        return cagr, None
    except Exception:
        return None, "INSUFFICIENT"
