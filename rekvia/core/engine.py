import pandas as pd
import os
import logging
from typing import Callable, Optional
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter

from rekvia.config.settings import load_settings
from rekvia.core.utils import (
    safe_float, safe_date, get_actual_column_name, normalize, validate_gstin,
    determine_tax_structure, smart_invoice_match
)

logger = logging.getLogger("rekvia")

def analyze_status(row: pd.Series, tolerance: float) -> str:
    if pd.notna(row.get('Match_Type')) and row['Match_Type'] == 'Smart Match': return "Matched (Smart)"
    if row['_merge'] == 'both':
        if abs(row.get('Total_Tax_PR', 0) - row.get('Total_Tax_2B', 0)) <= tolerance: return "Matched"
        return "Mismatch in Value"
    elif row['_merge'] == 'left_only': return "Missing in GSTR-2B"
    return "Not in Purchase Register"

def assign_risk(status: str, valid_gstin: bool) -> str:
    if not valid_gstin: return "HIGH (Invalid GSTIN)"
    if status == 'Missing in GSTR-2B': return "HIGH"
    if status == 'Mismatch in Value': return "MEDIUM"
    return "LOW"

def get_col(cols_map: dict, key: str, suffix: str) -> Optional[str]:
    val = cols_map.get(key)
    return val + suffix if val else None

def run_logic(file_books: str, file_2b: str, logger_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
    def _log(msg: str):
        logger.info(msg)
        if logger_callback:
            logger_callback(msg)

    _log("Loading Excel files...")
    try:
        df_books = pd.read_excel(file_books)
        df_2b = pd.read_excel(file_2b)
    except Exception as e:
        _log(f"ERROR: File corrupted or protected.\nDetail: {e}")
        logger.error("File load error", exc_info=True)
        return None

    settings = load_settings()
    BOOK_COLUMN_ALIASES = settings.get("BOOK_COLUMN_ALIASES", {})
    GSTR2B_COLUMN_ALIASES = settings.get("GSTR2B_COLUMN_ALIASES", {})
    TOLERANCE = settings.get("TOLERANCE", 2.0)

    # MAP COLUMNS
    _log("Mapping columns...")
    COLS_BOOKS = {}
    missing_cols_books = []
    for key, alias_list in BOOK_COLUMN_ALIASES.items():
        actual_name = get_actual_column_name(df_books, alias_list)
        if actual_name: COLS_BOOKS[key] = actual_name
        elif key in ['gstin', 'inv_no', 'value']: missing_cols_books.append(key)
    
    COLS_2B = {}
    missing_cols_2b = []
    for key, alias_list in GSTR2B_COLUMN_ALIASES.items():
        actual_name = get_actual_column_name(df_2b, alias_list)
        if actual_name: COLS_2B[key] = actual_name
        elif key in ['gstin', 'inv_no', 'value']: missing_cols_2b.append(key)

    if missing_cols_books or missing_cols_2b:
        _log(f"CRITICAL ERROR: Missing columns.\nBooks: {missing_cols_books}\n2B: {missing_cols_2b}")
        return None

    _log("Cleaning & Normalizing Data...")
    
    # PROCESSING BOOKS
    df_books['Clean_GSTIN'] = df_books[COLS_BOOKS['gstin']].apply(lambda x: str(x).strip().upper())
    df_books['Clean_Inv'] = df_books[COLS_BOOKS['inv_no']].apply(normalize)
    df_books['GSTIN_Valid'] = df_books['Clean_GSTIN'].apply(validate_gstin)
    
    if 'date' in COLS_BOOKS:
        df_books['Formatted_Date'] = df_books[COLS_BOOKS['date']].apply(safe_date)

    df_books['Total_Tax'] = 0.0
    for t in ['tax_cgst', 'tax_sgst', 'tax_igst']:
        col = COLS_BOOKS.get(t)
        if col: 
            df_books[col] = df_books[col].apply(safe_float)
            df_books['Total_Tax'] += df_books[col]
            
    df_books['Tax_Structure'] = df_books.apply(
        lambda x: determine_tax_structure(x, COLS_BOOKS.get('tax_cgst'), COLS_BOOKS.get('tax_igst')), axis=1
    )
    df_books['Tax_Round'] = df_books['Total_Tax'].round(0)

    # PROCESSING 2B
    df_2b['Clean_GSTIN'] = df_2b[COLS_2B['gstin']].apply(lambda x: str(x).strip().upper())
    df_2b['Clean_Inv'] = df_2b[COLS_2B['inv_no']].apply(normalize)
    
    if 'date' in COLS_2B:
        df_2b['Formatted_Date'] = df_2b[COLS_2B['date']].apply(safe_date)

    cols_2b_tax = [COLS_2B.get('tax_cgst'), COLS_2B.get('tax_sgst'), COLS_2B.get('tax_igst')]
    df_2b['Total_Tax'] = 0.0
    for col in cols_2b_tax:
        if col:
            df_2b[col] = df_2b[col].apply(safe_float)
            df_2b['Total_Tax'] += df_2b[col]
        
    df_2b['Tax_Structure'] = df_2b.apply(
        lambda x: determine_tax_structure(x, COLS_2B.get('tax_cgst'), COLS_2B.get('tax_igst')), axis=1
    )
    df_2b['Tax_Round'] = df_2b['Total_Tax'].round(0)

    # Key Creation
    df_books['Key'] = df_books['Clean_GSTIN'] + "_" + df_books['Clean_Inv']
    df_2b['Key'] = df_2b['Clean_GSTIN'] + "_" + df_2b['Clean_Inv']

    # Implement exact one-to-one matching to prevent Cartesian product duplication
    df_books['Key_Unique'] = df_books['Key'] + "_" + df_books.groupby('Key').cumcount().astype(str)
    df_2b['Key_Unique'] = df_2b['Key'] + "_" + df_2b.groupby('Key').cumcount().astype(str)

    df_books = df_books.add_suffix('_PR')
    df_2b = df_2b.add_suffix('_2B')
    df_books.rename(columns={'Key_Unique_PR': 'Key_Unique'}, inplace=True)
    df_2b.rename(columns={'Key_Unique_2B': 'Key_Unique'}, inplace=True)

    _log("Running Matching Logic...")
    merged = pd.merge(df_books, df_2b, on='Key_Unique', how='outer', indicator=True)

    matched = merged[merged['_merge'] == 'both'].copy()
    unmatched = merged[merged['_merge'] != 'both'].copy()
    books_unmatched = unmatched[unmatched['_merge'] == 'left_only'].copy()
    gstr2b_unmatched = unmatched[unmatched['_merge'] == 'right_only'].copy()
    
    new_matches = []
    matched_2b_indices = set()
    lookup_2b = {}
    
    for idx, row in gstr2b_unmatched.iterrows():
        # Group solely by GSTIN, not integer rounded tax, to ensure tolerance captures border cases
        lookup_key = row['Clean_GSTIN_2B']
        if lookup_key not in lookup_2b: lookup_2b[lookup_key] = []
        lookup_2b[lookup_key].append((idx, row))

    count_smart = 0
    for _, row_pr in books_unmatched.iterrows():
        lookup_key = row_pr['Clean_GSTIN_PR']
        candidates = lookup_2b.get(lookup_key, [])
        found = False
        
        for idx_2b, row_2b in candidates:
            if idx_2b in matched_2b_indices: continue
            if abs(row_pr['Total_Tax_PR'] - row_2b['Total_Tax_2B']) <= TOLERANCE:
                if smart_invoice_match(row_pr['Clean_Inv_PR'], row_2b['Clean_Inv_2B']):
                    combined = row_pr.combine_first(row_2b)
                    combined['_merge'] = 'both'
                    combined['Match_Type'] = 'Smart Match'
                    if row_pr['Tax_Structure_PR'] != row_2b['Tax_Structure_2B']:
                        combined['Observation'] = 'Tax Head Mismatch'
                    new_matches.append(combined)
                    matched_2b_indices.add(idx_2b)
                    found = True
                    count_smart += 1
                    break
        if not found:
            row_pr['Match_Type'] = 'Unmatched'
            new_matches.append(row_pr)

    _log(f"  -> Smart matches found: {count_smart}")

    remaining_2b = gstr2b_unmatched.drop(index=list(matched_2b_indices))
    remaining_2b['Match_Type'] = 'Unmatched'
    final_df = pd.concat([matched, pd.DataFrame(new_matches), remaining_2b], ignore_index=True)

    _log("Generating Report...")
    
    final_df['Status'] = final_df.apply(lambda r: analyze_status(r, TOLERANCE), axis=1)
    
    # Handle NaN in boolean column cleanly
    if 'GSTIN_Valid_PR' in final_df.columns:
        final_df['GSTIN_Valid_PR'] = final_df['GSTIN_Valid_PR'].fillna(True).astype(bool)

    final_df['Risk_Level'] = final_df.apply(lambda x: assign_risk(x.get('Status', ''), x.get('GSTIN_Valid_PR', True)), axis=1)

    # EXPORT
    output_filename = "Rekvia_Reconciliation_Report.xlsx"
    output_path = os.path.join(os.path.dirname(file_books), output_filename)

    # Identify Columns
    col_gstin_pr = 'Clean_GSTIN_PR'
    col_inv_pr = get_col(COLS_BOOKS, 'inv_no', '_PR')
    col_date_pr = 'Formatted_Date_PR' if 'Formatted_Date_PR' in final_df.columns else get_col(COLS_BOOKS, 'date', '_PR')
    col_val_pr = get_col(COLS_BOOKS, 'value', '_PR')
    col_tax_pr = 'Total_Tax_PR'
    col_vendor_pr = get_col(COLS_BOOKS, 'vendor', '_PR')

    col_gstin_2b = 'Clean_GSTIN_2B'
    col_inv_2b = get_col(COLS_2B, 'inv_no', '_2B')
    col_date_2b = 'Formatted_Date_2B' if 'Formatted_Date_2B' in final_df.columns else get_col(COLS_2B, 'date', '_2B')
    col_val_2b = get_col(COLS_2B, 'value', '_2B')
    col_tax_2b = 'Total_Tax_2B'
    col_vendor_2b = get_col(COLS_2B, 'vendor', '_2B')
    col_itc_2b = get_col(COLS_2B, 'itc', '_2B')
    col_rcm_2b = get_col(COLS_2B, 'rcm', '_2B')

    # Define Column Lists
    cols_combined = [
        'Status', 'Risk_Level', 'Match_Type', 'Observation',
        col_gstin_pr, col_gstin_2b, col_vendor_pr, col_vendor_2b,
        col_inv_pr, col_inv_2b, col_date_pr, col_date_2b,
        col_val_pr, col_val_2b, col_tax_pr, col_tax_2b,
        col_itc_2b, col_rcm_2b
    ]
    cols_pr_only = ['Status', 'Clean_GSTIN_PR', col_vendor_pr, col_inv_pr, col_date_pr, col_val_pr, col_tax_pr]
    cols_2b_only = ['Status', 'Clean_GSTIN_2B', col_vendor_2b, col_inv_2b, col_date_2b, col_val_2b, col_tax_2b, col_itc_2b, col_rcm_2b]

    final_cols_combined = [c for c in cols_combined if c and c in final_df.columns]
    final_cols_pr = [c for c in cols_pr_only if c and c in final_df.columns]
    final_cols_2b = [c for c in cols_2b_only if c and c in final_df.columns]

    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            final_df['Status'].value_counts().reset_index().to_excel(writer, sheet_name='Summary', index=False)
            
            matched_df = final_df[final_df['Status'].str.contains('Matched', na=False)]
            if not matched_df.empty:
                matched_df[final_cols_combined].to_excel(writer, sheet_name='Matched (Combined)', index=False)
                matched_df[final_cols_pr].to_excel(writer, sheet_name='Matched (PR View)', index=False)
                matched_df[final_cols_2b].to_excel(writer, sheet_name='Matched (2B View)', index=False)

            sheet_map = {
                'Missing in 2B': final_df[final_df['Status'] == 'Missing in GSTR-2B'],
                'Not in Books': final_df[final_df['Status'] == 'Not in Purchase Register'],
                'Mismatches': final_df[final_df['Status'] == 'Mismatch in Value']
            }
            for sheet_name, data in sheet_map.items():
                if not data.empty:
                    data[final_cols_combined].to_excel(writer, sheet_name=sheet_name, index=False)

            for sheet in writer.sheets:
                ws = writer.sheets[sheet]
                ws.freeze_panes = "A2"
                for col in ws.columns:
                    ws.column_dimensions[get_column_letter(col[0].column)].width = 18
        
        _log(f"\nSUCCESS! Report saved to:\n{output_path}")
        return output_path

    except PermissionError:
        _log(f"\nERROR: Please close '{output_filename}' and try again.")
        logger.error(f"Permission error saving {output_path}")
        return None
