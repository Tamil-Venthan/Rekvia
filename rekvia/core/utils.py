import pandas as pd
import re
from typing import Any, Optional, Dict, List

def safe_float(value: Any) -> float:
    """Safely converts a given value to float. Returns 0.0 if not possible."""
    if pd.isna(value): return 0.0
    s = str(value).strip().lower()
    if s in ['nil', 'na', '-', '']: return 0.0
    
    is_negative = False
    if s.startswith('(') and s.endswith(')'):
        is_negative = True
    elif '-' in s:
        is_negative = True
        
    s_clean = re.sub(r'[^\d.]', '', s)
    try: 
        val = float(s_clean)
        return -val if is_negative else val
    except ValueError: return 0.0

def safe_date(value: Any) -> str:
    """Formats a date safely, converting it to YYYY-MM-DD string."""
    if pd.isna(value): return ""
    try: return pd.to_datetime(value).strftime('%Y-%m-%d')
    except Exception: return str(value)

def get_actual_column_name(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
    """Tries to find the actual column name in the DataFrame from a list of possible names."""
    df_cols_lower = {str(c).strip().lower(): c for c in df.columns}
    for name in possible_names:
        clean_name = name.strip().lower()
        if clean_name in df_cols_lower: return df_cols_lower[clean_name]
    return None 

def normalize(text: Any) -> str:
    """Normalizes text by removing non-alphanumeric characters and converting to uppercase."""
    if pd.isna(text): return ""
    return re.sub(r'[^A-Z0-9]', '', str(text).upper())

def validate_gstin(gstin: Any) -> bool:
    """Validates the structure of a given GSTIN."""
    if pd.isna(gstin): return False
    pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}$'
    return bool(re.match(pattern, str(gstin).strip().upper()))

def determine_tax_structure(row: pd.Series, cgst_col: Optional[str], igst_col: Optional[str]) -> str:
    """Determines the tax structure based on available GST amounts."""
    if igst_col and row.get(igst_col, 0) > 0.1: return "IGST"
    elif cgst_col and row.get(cgst_col, 0) > 0.1: return "CGST+SGST"
    return "Zero/Exempt"

def smart_invoice_match(inv1: Any, inv2: Any) -> bool:
    """Applies fuzzy matching logic to decide if two invoices represent the same document."""
    a, b = normalize(inv1), normalize(inv2)
    if not a or not b: return False
    if a == b: return True
    if a.endswith(b) or b.endswith(a): return True
    # Strip basic years from the string and check if the remaining parts match
    a_cl = re.sub(r'20\d{2}|2\d2\d', '', a)
    b_cl = re.sub(r'20\d{2}|2\d2\d', '', b)
    if a_cl == b_cl and len(a_cl) > 2: return True
    return False
