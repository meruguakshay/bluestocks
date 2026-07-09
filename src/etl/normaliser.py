import re

def normalize_year(val) -> int:
    """
    Standardize various year representations to a 4-digit integer.
    E.g., "FY23" -> 2023, "2022-23" -> 2023, "2023" -> 2023, "23" -> 2023, "FY 2022-2023" -> 2023.
    Returns None if cannot be parsed.
    """
    if val is None:
        return None
    
    # Convert to string and clean
    s = str(val).strip()
    if not s:
        return None
        
    # Remove "FY" or "FY " prefix (case-insensitive)
    s = re.sub(r'(?i)\bFY\b', '', s).strip()
    s = re.sub(r'(?i)\bFY\s*', '', s).strip()
    
    # Handle range formats like "2022-23" or "2022-2023" or "2022/23"
    if '-' in s:
        parts = s.split('-')
        s = parts[1].strip()
    elif '/' in s:
        parts = s.split('/')
        s = parts[1].strip()
        
    # Search for a 4-digit year starting with 19 or 20 (e.g. 2023 or 2016)
    match_4d = re.search(r'\b(19|20)\d{2}\b', s)
    if match_4d:
        return int(match_4d.group(0))
        
    # Extract digit-only characters
    s = re.sub(r'\D', '', s)
    if not s:
        return None
        
    # If 2 digits, convert to 4 digits (assume 20xx for >= 00, adjust if needed)
    if len(s) == 2:
        val_int = int(s)
        # Assuming years 2000-2099
        return 2000 + val_int
    elif len(s) == 4:
        return int(s)
    elif len(s) > 4:
        # Take the last 4 digits
        return int(s[-4:])
    else:
        return None

def normalize_ticker(val) -> str:
    """
    Standardize ticker codes to a clean uppercase string without suffixes like .NS or .BO.
    E.g., "reliance.ns" -> "RELIANCE", " 500325.bo  " -> "500325", "tcs" -> "TCS".
    Returns None if empty.
    """
    if val is None:
        return None
    s = str(val).strip().upper()
    if not s:
        return None
        
    # Remove exchange suffixes like .NS, .BO, .BOX, etc.
    s = re.sub(r'\.(NS|BO|NS|BO|COM|NET|ORG)$', '', s)
    
    # Remove any non-alphanumeric characters except spaces/hyphens
    s = re.sub(r'[^A-Z0-9\-]', '', s)
    
    return s if s else None
