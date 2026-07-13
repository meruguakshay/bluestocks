import pandas as pd

def calculate_fcf(cfo, cfi):
    """
    Free Cash Flow: CFO + CFI
    """
    if cfo is None or pd.isna(cfo) or cfi is None or pd.isna(cfi):
        return None
    return float(cfo) + float(cfi)

def calculate_cfo_quality(cfo_history, pat_history):
    """
    CFO Quality Score: CFO / PAT ratio averaged over 5 years.
    Returns (avg_ratio, label)
    
    Labels:
    - >1.0 = High Quality
    - 0.5-1.0 = Moderate
    - <0.5 = Accrual Risk
    - return None if PAT = 0 in current year
    """
    if not cfo_history or not pat_history:
        return None, None
    if len(cfo_history) < 5 or len(pat_history) < 5:
        return None, None
        
    current_pat = pat_history[-1]
    if current_pat is None or pd.isna(current_pat) or current_pat == 0.0:
        return None, None
        
    ratios = []
    for cfo, pat in zip(cfo_history[-5:], pat_history[-5:]):
        if cfo is None or pd.isna(cfo) or pat is None or pd.isna(pat) or pat == 0.0:
            continue
        ratios.append(float(cfo) / float(pat))
        
    if not ratios:
        return None, None
        
    avg_ratio = sum(ratios) / len(ratios)
    
    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
        
    return avg_ratio, label

def calculate_capex_intensity(cfi, sales):
    """
    CapEx Intensity: abs(investing_activity) / sales x 100
    Returns (capex_pct, label)
    
    Labels:
    - <3% = Asset Light
    - 3-8% = Moderate
    - >8% = Capital Intensive
    """
    if cfi is None or pd.isna(cfi) or sales is None or pd.isna(sales) or sales == 0.0:
        return None, None
        
    capex_pct = (abs(float(cfi)) / float(sales)) * 100.0
    
    if capex_pct < 3.0:
        label = "Asset Light"
    elif capex_pct <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"
        
    return capex_pct, label

def calculate_fcf_conversion(fcf, operating_profit):
    """
    FCF Conversion Rate: FCF / operating_profit x 100
    """
    if fcf is None or pd.isna(fcf) or operating_profit is None or pd.isna(operating_profit) or operating_profit == 0.0:
        return None
    return (float(fcf) / float(operating_profit)) * 100.0

def classify_capital_allocation(cfo, cfi, cff, net_profit):
    """
    Capital allocation 8-pattern classifier based on signs of (CFO, CFI, CFF)
    where >= 0 is '+' and < 0 is '-'
    
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label)
    """
    if cfo is None or pd.isna(cfo) or cfi is None or pd.isna(cfi) or cff is None or pd.isna(cff):
        return None, None, None, "Unknown"
        
    cfo_sign = "+" if float(cfo) >= 0.0 else "-"
    cfi_sign = "+" if float(cfi) >= 0.0 else "-"
    cff_sign = "+" if float(cff) >= 0.0 else "-"
    
    # Check high CFO/PAT
    is_high_cfo_pat = False
    if net_profit is not None and pd.notna(net_profit) and net_profit > 0.0:
        if (float(cfo) / float(net_profit)) > 1.0:
            is_high_cfo_pat = True
            
    # Classify pattern
    if cfo_sign == "+" and cfi_sign == "-" and cff_sign == "-":
        if is_high_cfo_pat:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif cfo_sign == "+" and cfi_sign == "+" and cff_sign == "-":
        label = "Liquidating Assets"
    elif cfo_sign == "-" and cfi_sign == "+" and cff_sign == "+":
        label = "Distress Signal"
    elif cfo_sign == "-" and cfi_sign == "-" and cff_sign == "+":
        label = "Growth Funded by Debt"
    elif cfo_sign == "+" and cfi_sign == "+" and cff_sign == "+":
        label = "Cash Accumulator"
    elif cfo_sign == "-" and cfi_sign == "-" and cff_sign == "-":
        label = "Pre-Revenue"
    elif cfo_sign == "+" and cfi_sign == "-" and cff_sign == "+":
        label = "Mixed"
    elif cfo_sign == "-" and cfi_sign == "+" and cff_sign == "-":
        label = "Distress Signal"  # CFO < 0 is a distress signal
    else:
        label = "Mixed"
        
    return cfo_sign, cfi_sign, cff_sign, label
