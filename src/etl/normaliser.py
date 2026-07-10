import re
from typing import Optional

def normalize_year(val) -> Optional[str]:
    """
    Standardize various year representations to YYYY-MM format.
    E.g., "FY23" -> "2023-03", "2022-23" -> "2023-03", "2023" -> "2023-03", "23" -> "2023-03", 
          "Dec-22" -> "2022-12", "Jun-23" -> "2023-06", "March-2023" -> "2023-03", "2023-03" -> "2023-03".
    Returns None if cannot be parsed.
    """
    if val is None:
        return None
    
    # Convert to string and clean
    s = str(val).strip()
    if not s:
        return None
        
    # Already normalised (matches YYYY-MM where MM is 01-12)?
    if re.match(r'^\d{4}-(0[1-9]|1[0-2])$', s):
        return s
        
    # Check for TTM (Trailing Twelve Months) - should not match year formats
    if s.upper() == 'TTM':
        return None
        
    # Remove "FY" or "FY " or "FY-" prefix (case-insensitive)
    s = re.sub(r'(?i)\bFY[\s-]*', '', s).strip()
    
    # Months lookup mapping
    months_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
        'january': '01', 'february': '02', 'march': '03', 'april': '04', 'june': '06',
        'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    # 1. Match month abbreviation/name and 2 or 4-digit year (e.g. "Mar-23", "Dec 2022", "March-2023")
    match_my = re.search(r'(?i)([a-z]{3,})\b[\s-]*(\d{2,4})', s)
    if match_my:
        m_name = match_my.group(1).lower()
        yr_part = match_my.group(2)
        if m_name in months_map:
            m_num = months_map[m_name]
            if len(yr_part) == 2:
                yr = 2000 + int(yr_part)
            else:
                yr = int(yr_part)
            return f"{yr:04d}-{m_num}"
            
    # 2. Match reversed month format (e.g., "23-Mar", "2023-March")
    match_ym = re.search(r'(?i)(\d{2,4})[\s-]*([a-z]{3,})\b', s)
    if match_ym:
        yr_part = match_ym.group(1)
        m_name = match_ym.group(2).lower()
        if m_name in months_map:
            m_num = months_map[m_name]
            if len(yr_part) == 2:
                yr = 2000 + int(yr_part)
            else:
                yr = int(yr_part)
            return f"{yr:04d}-{m_num}"
            
    # 3. Handle pure numeric or range years (e.g., "2023", "23", "2022-23", "2022/2023")
    # In range formats, the second part signifies the end year
    if '-' in s:
        parts = s.split('-')
        s = parts[-1].strip()
    elif '/' in s:
        parts = s.split('/')
        s = parts[-1].strip()
        
    # Search for any remaining digits
    digits = re.sub(r'\D', '', s)
    if digits:
        if len(digits) == 2:
            yr = 2000 + int(digits)
            return f"{yr:04d}-03" # Assume March close by default
        elif len(digits) == 4:
            yr = int(digits)
            return f"{yr:04d}-03" # Assume March close by default
        elif len(digits) > 4:
            yr = int(digits[-4:])
            return f"{yr:04d}-03" # Assume March close by default

    return None

def normalize_ticker(val) -> Optional[str]:
    """
    Standardize ticker codes to a clean uppercase string without suffixes like .NS or .BO.
    Preserves hyphens and ampersands for valid tickers (e.g., "M&M", "BAJAJ-AUTO").
    Returns None if empty.
    """
    if val is None:
        return None
    s = str(val).strip().upper()
    if not s:
        return None
        
    # Remove exchange suffixes like .NS, .BO, .COM, etc.
    s = re.sub(r'\.(NS|BO|COM|NET|ORG)$', '', s)
    
    # Remove any non-alphanumeric characters except hyphens and ampersands
    s = re.sub(r'[^A-Z0-9\-&]', '', s)
    
    return s if s else None
