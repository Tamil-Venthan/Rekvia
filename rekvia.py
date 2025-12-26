import pandas as pd
import re
import os
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, scrolledtext
from openpyxl.utils import get_column_letter

# ==========================================
# 0. USER CONFIGURATION (UPDATE LINKS HERE)
# ==========================================
CONTACT_LINKS = {
    "telegram": "https://t.me/tamilventhan4", 
    "linkedin": "https://www.linkedin.com/in/tamil-venthan4/",
    "github": "https://github.com/Tamil-Venthan"
}

# ==========================================
# 1. SYSTEM CONFIGURATION & HELPERS
# ==========================================
try:
    pd.set_option('future.no_silent_downcasting', True)
except Exception:
    pass

BOOK_COLUMN_ALIASES = {
    'gstin': ['GSTIN/UIN', 'GSTIN', 'GST Number', 'Supplier GSTIN', 'Tin No', 'Party GSTIN'],
    'inv_no': ['Voucher Ref. No.', 'Invoice No', 'Invoice Number', 'Bill No', 'Doc No', 'Ref No'],
    'date': ['Voucher Ref. Date', 'Invoice Date', 'Bill Date', 'Doc Date', 'Date'],
    'tax_cgst': ['INPUT CGST', 'CGST', 'Central Tax', 'CGST Amount', 'CGST Amt'],
    'tax_sgst': ['INPUT SGST', 'SGST', 'State/UT Tax', 'SGST Amount', 'SGST Amt'],
    'tax_igst': ['INPUT IGST', 'IGST', 'Integrated Tax', 'IGST Amount', 'IGST Amt'],
    'value': ['Value', 'Taxable Value', 'Taxable Amount', 'Gross Value', 'Net Amount'],
    'vendor': ['Buyer/Supplier', 'Party Name', 'Supplier Name', 'Vendor Name', 'Trade Name', 'Particulars']
}

GSTR2B_COLUMN_ALIASES = {
    'gstin': ['GSTIN of supplier', 'GSTIN', 'Supplier GSTIN'],
    'inv_no': ['Invoice number', 'Invoice No', 'Inv No'],
    'date': ['Invoice Date', 'Inv Date', 'Date'],
    'tax_cgst': ['Central Tax(₹)', 'Central Tax', 'CGST', 'CGST(₹)'],
    'tax_sgst': ['State/UT Tax(₹)', 'State/UT Tax', 'SGST', 'SGST(₹)'],
    'tax_igst': ['Integrated Tax(₹)', 'Integrated Tax', 'IGST', 'IGST(₹)'],
    'value': ['Taxable Value (₹)', 'Taxable Value', 'Taxable Amt'],
    'vendor': ['Trade/Legal name', 'Trade Name', 'Legal Name', 'Name'],
    'itc': ['ITC Availability', 'ITC Available', 'Eligibility for ITC', 'ITC Status'],
    'rcm': ['Reverse Charge', 'RCM', 'Reverse Charge Mechanism']
}

TOLERANCE = 2.0 

# --- SAFETY FUNCTIONS ---
def safe_float(value):
    if pd.isna(value): return 0.0
    s = str(value).strip().lower()
    if s in ['nil', 'na', '-', '']: return 0.0
    s_clean = re.sub(r'[^\d.-]', '', s)
    try: return float(s_clean)
    except ValueError: return 0.0

def safe_date(value):
    if pd.isna(value): return ""
    try: return pd.to_datetime(value).strftime('%Y-%m-%d')
    except Exception: return str(value)

def get_actual_column_name(df, possible_names):
    df_cols_lower = {str(c).strip().lower(): c for c in df.columns}
    for name in possible_names:
        clean_name = name.strip().lower()
        if clean_name in df_cols_lower: return df_cols_lower[clean_name]
    return None 

def normalize(text):
    if pd.isna(text): return ""
    return re.sub(r'[^A-Z0-9]', '', str(text).upper())

def validate_gstin(gstin):
    if pd.isna(gstin): return False
    pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}$'
    return bool(re.match(pattern, str(gstin).strip().upper()))

def determine_tax_structure(row, cgst_col, igst_col):
    if row.get(igst_col, 0) > 0.1: return "IGST"
    elif row.get(cgst_col, 0) > 0.1: return "CGST+SGST"
    return "Zero/Exempt"

def smart_invoice_match(inv1, inv2):
    a, b = normalize(inv1), normalize(inv2)
    if not a or not b: return False
    if a == b: return True
    if a.endswith(b) or b.endswith(a): return True
    a_cl = re.sub(r'20\d{2}|2\d2\d', '', a)
    b_cl = re.sub(r'20\d{2}|2\d2\d', '', b)
    if a_cl == b_cl and len(a_cl) > 2: return True
    return False

# ==========================================
# 2. PROCESSING LOGIC
# ==========================================
def run_logic(file_books, file_2b, logger_func):
    logger_func("Loading Excel files...")
    try:
        df_books = pd.read_excel(file_books)
        df_2b = pd.read_excel(file_2b)
    except Exception as e:
        logger_func(f"ERROR: File corrupted or protected.\nDetail: {e}")
        return

    # --- MAP COLUMNS ---
    logger_func("Mapping columns...")
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
        logger_func(f"CRITICAL ERROR: Missing columns.\nBooks: {missing_cols_books}\n2B: {missing_cols_2b}")
        return

    logger_func("Cleaning & Normalizing Data...")
    
    # --- PROCESSING BOOKS ---
    df_books['Clean_GSTIN'] = df_books[COLS_BOOKS['gstin']].apply(lambda x: str(x).strip().upper())
    df_books['Clean_Inv'] = df_books[COLS_BOOKS['inv_no']].apply(normalize)
    df_books['GSTIN_Valid'] = df_books['Clean_GSTIN'].apply(validate_gstin)
    
    if 'date' in COLS_BOOKS:
        df_books['Formatted_Date'] = df_books[COLS_BOOKS['date']].apply(safe_date)

    df_books['Total_Tax'] = 0
    for t in ['tax_cgst', 'tax_sgst', 'tax_igst']:
        col = COLS_BOOKS.get(t)
        if col: 
            df_books[col] = df_books[col].apply(safe_float)
            df_books['Total_Tax'] += df_books[col]
            
    df_books['Tax_Structure'] = df_books.apply(
        lambda x: determine_tax_structure(x, COLS_BOOKS.get('tax_cgst'), COLS_BOOKS.get('tax_igst')), axis=1
    )
    df_books['Tax_Round'] = df_books['Total_Tax'].round(0)

    # --- PROCESSING 2B ---
    df_2b['Clean_GSTIN'] = df_2b[COLS_2B['gstin']].apply(lambda x: str(x).strip().upper())
    df_2b['Clean_Inv'] = df_2b[COLS_2B['inv_no']].apply(normalize)
    
    if 'date' in COLS_2B:
        df_2b['Formatted_Date'] = df_2b[COLS_2B['date']].apply(safe_date)

    cols_2b_tax = [COLS_2B.get('tax_cgst'), COLS_2B.get('tax_sgst'), COLS_2B.get('tax_igst')]
    df_2b['Total_Tax'] = 0
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

    df_books = df_books.add_suffix('_PR')
    df_2b = df_2b.add_suffix('_2B')
    df_books.rename(columns={'Key_PR': 'Key'}, inplace=True)
    df_2b.rename(columns={'Key_2B': 'Key'}, inplace=True)

    logger_func("Running Matching Logic...")
    merged = pd.merge(df_books, df_2b, on='Key', how='outer', indicator=True)

    matched = merged[merged['_merge'] == 'both'].copy()
    unmatched = merged[merged['_merge'] != 'both'].copy()
    books_unmatched = unmatched[unmatched['_merge'] == 'left_only'].copy()
    gstr2b_unmatched = unmatched[unmatched['_merge'] == 'right_only'].copy()
    
    new_matches = []
    matched_2b_indices = set()
    lookup_2b = {}
    
    for idx, row in gstr2b_unmatched.iterrows():
        lookup_key = (row['Clean_GSTIN_2B'], row['Tax_Round_2B'])
        if lookup_key not in lookup_2b: lookup_2b[lookup_key] = []
        lookup_2b[lookup_key].append((idx, row))

    count_smart = 0
    for _, row_pr in books_unmatched.iterrows():
        lookup_key = (row_pr['Clean_GSTIN_PR'], row_pr['Tax_Round_PR'])
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

    logger_func(f"  -> Smart matches found: {count_smart}")

    remaining_2b = gstr2b_unmatched.drop(index=list(matched_2b_indices))
    remaining_2b['Match_Type'] = 'Unmatched'
    final_df = pd.concat([matched, pd.DataFrame(new_matches), remaining_2b], ignore_index=True)

    logger_func("Generating Report...")
    
    def analyze_status(row):
        if pd.notna(row.get('Match_Type')) and row['Match_Type'] == 'Smart Match': return "Matched (Smart)"
        if row['_merge'] == 'both':
            if abs(row['Total_Tax_PR'] - row['Total_Tax_2B']) <= TOLERANCE: return "Matched"
            return "Mismatch in Value"
        elif row['_merge'] == 'left_only': return "Missing in GSTR-2B"
        return "Not in Purchase Register"

    final_df['Status'] = final_df.apply(analyze_status, axis=1)
    final_df.loc[final_df['GSTIN_Valid_PR'].isna(), 'GSTIN_Valid_PR'] = True
    final_df['GSTIN_Valid_PR'] = final_df['GSTIN_Valid_PR'].astype(bool)

    def assign_risk(status, valid_gstin):
        if not valid_gstin: return "HIGH (Invalid GSTIN)"
        if status == 'Missing in GSTR-2B': return "HIGH"
        if status == 'Mismatch in Value': return "MEDIUM"
        return "LOW"
    
    final_df['Risk_Level'] = final_df.apply(lambda x: assign_risk(x['Status'], x['GSTIN_Valid_PR']), axis=1)

    # EXPORT
    output_filename = "Rekvia_Reconciliation_Report.xlsx"
    output_path = os.path.join(os.path.dirname(file_books), output_filename)
    
    def get_col(cols_map, key, suffix):
        val = cols_map.get(key)
        return val + suffix if val else None

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
            
            matched_df = final_df[final_df['Status'].str.contains('Matched')]
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
        
        logger_func(f"\nSUCCESS! Report saved to:\n{output_path}")
        return output_path

    except PermissionError:
        logger_func(f"\nERROR: Please close '{output_filename}' and try again.")
        return None

# ==========================================
# 3. GUI CLASS
# ==========================================
class GSTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rekvia - GST Reconciliation Tool")
        self.root.geometry("400x550") 
        
        self.path_books = tk.StringVar()
        self.path_2b = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        # Header
        lbl_title = tk.Label(self.root, text="Rekvia - Automated Reconciliation", font=("Arial", 16, "bold"), fg="#333")
        lbl_title.pack(pady=10)

        frame_files = tk.Frame(self.root, padx=20)
        frame_files.pack(fill="x")
        
        tk.Label(frame_files, text="Purchase Register (Books):").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_files, textvariable=self.path_books, width=50).grid(row=1, column=0, pady=5)
        tk.Button(frame_files, text="Browse", command=self.browse_books).grid(row=1, column=1, padx=5)

        tk.Label(frame_files, text="GSTR-2B File:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        tk.Entry(frame_files, textvariable=self.path_2b, width=50).grid(row=3, column=0, pady=5)
        tk.Button(frame_files, text="Browse", command=self.browse_2b).grid(row=3, column=1, padx=5)

        btn_run = tk.Button(self.root, text="Start Reconciliation", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), height=2, command=self.start_process)
        btn_run.pack(pady=15, fill="x", padx=20)

        tk.Label(self.root, text="Process Log:").pack(anchor="w", padx=20)
        self.txt_log = scrolledtext.ScrolledText(self.root, height=12, state='disabled', font=("Consolas", 9))
        self.txt_log.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Social Buttons
        frame_social = tk.Frame(self.root)
        frame_social.pack(pady=10, fill="x")
        
        tk.Label(frame_social, text="Any suggestions? Contact:", font=("Arial", 9, "bold")).pack(pady=(0, 5))

        btn_tg = tk.Button(frame_social, text="Telegram", bg="#0088cc", fg="white", width=12, command=lambda: self.open_link('telegram'))
        btn_tg.pack(side="left", padx=20)

        btn_gh = tk.Button(frame_social, text="GitHub", bg="#0088cc", fg="white", width=12, command=lambda: self.open_link('github'))
        btn_gh.pack(side="left", padx=20)

        btn_li = tk.Button(frame_social, text="LinkedIn", bg="#0077b5", fg="white", width=12, command=lambda: self.open_link('linkedin'))
        btn_li.pack(side="left", padx=20)

    def browse_books(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if filename: self.path_books.set(filename)

    def browse_2b(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if filename: self.path_2b.set(filename)

    def log(self, message):
        self.txt_log.config(state='normal')
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')

    def open_link(self, key):
        url = CONTACT_LINKS.get(key)
        if url: webbrowser.open(url)

    def start_process(self):
        p_books = self.path_books.get()
        p_2b = self.path_2b.get()
        if not p_books or not p_2b:
            messagebox.showwarning("Missing Files", "Please select both files.")
            return
        if not os.path.exists(p_books) or not os.path.exists(p_2b):
            messagebox.showerror("Error", "Files not found.")
            return

        self.log("\nStarting Rekvia Engine...")
        threading.Thread(target=self.run_thread, args=(p_books, p_2b)).start()

    def run_thread(self, p_books, p_2b):
        output_file = run_logic(p_books, p_2b, self.log)
        if output_file:
            self.root.after(0, lambda: self.ask_open_file(output_file))

    def ask_open_file(self, output_file):
        response = messagebox.askyesno("Success", "Rekvia has finished!\nDo you want to open the report?")
        if response: os.startfile(output_file)

if __name__ == "__main__":
    root = tk.Tk()
    app = GSTApp(root)
    root.mainloop()