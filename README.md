# Rekvia
Python-based automation tool for GST Reconciliation

**Rekvia** is a powerful, automated desktop tool designed for finance professionals to reconcile Purchase Registers with GSTR-2B files instantly.

![Rekvia Status](https://img.shields.io/badge/Status-v1.2-brightgreen) ![Python](https://img.shields.io/badge/Built%20With-Python-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## Key Features

### Beautiful Modern Interface
* **CustomTkinter GUI:** A sleek, fully featured desktop application interface replacing out-dated standard terminal prompts.
* **Dynamic Configuration Panel:** An embedded ⚙️ Settings panel allows you to customize Vendor/Invoice column aliases and tweak mathematical tolerances on-the-fly without ever touching code.
* **Over-The-Air (OTA) Updater:** Rekvia now features a stealth background updater! It automatically pings GitHub releases on startup and seamlessly patches your `.exe` file so you always have the latest tax logic.

### Intelligent Matching Engine
* **Fuzzy Logic Matching:** Uses advanced algorithms to match invoices even if there are minor spelling differences (e.g., "TATA SONS" vs "TATA SONS LTD" or `(1,250.00)` vs `-1250`).
* **Smart Tolerance Boundaries:** Safely isolates floating-point differences (configurable via the UI, default tolerance: ±₹2.00) to bridge fractional tax gaps.
* **Strict 1-to-1 Duplicate Prevention:** Explicit sequence identifiers prevent identical duplicate invoices from falsely generating a Cartesian product, keeping your books absolutely accurate.

### Robust Data Safety
* **Crash-Proof Processing:** Automatically fixes common Excel errors like "Text stored as numbers" (e.g., `1,25,000` becomes `125000.0`).
* **Date Normalization:** Standardizes varied date formats into a clean `YYYY-MM-DD` structure.
* **File Validation:** Prevents processing if files are corrupted or password-protected.

### Comprehensive Reporting
* **3-Way View:** Generates three matched sheets for deep analysis:
    1.  **Combined View:** Side-by-side comparison.
    2.  **Books View:** What *you* recorded.
    3.  **Portal View:** What in the *GSTR2B* data.
* **Compliance Ready:** Extracts **ITC Availability** and **Reverse Charge (RCM)** status directly from GSTR-2B.
* **Risk Analysis:** Automatically tags unmatched invoices as **HIGH**, **MEDIUM**, or **LOW** risk based on value and status.

## Installation & Usage

### Option 1: Run the Executable (No Python Required)
1.  Go to the [Releases](https://github.com/Tamil-Venthan/Rekvia/releases) page.
2.  Download `Rekvia.exe`.
3.  Double-click to run! If an OTA update is available later, the app will auto-patch itself.

### Option 2: Run from Source
1.  Clone the repository:
    ```bash
    git clone https://github.com/Tamil-Venthan/Rekvia.git
    cd Rekvia
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python main.py
    ```

### Option 3: Compile your own `.exe`
We have included a customized `PyInstaller` build script that automatically packs your UI assets!
1. (Optional) Place an `icon.ico` file in the root folder to customize your logo.
2. Run the compiler:
    ```bash
    python build.py
    ```
3. Your portable app will be instantly generated in `dist/Rekvia.exe`!

## Data Preparation Guide ( ⚠️ Imp step)

To ensure Rekvia works perfectly, please follow these simple steps to prepare your Excel files.

### 1️⃣ Preparing the Purchase Register (from Tally)
If you are exporting data from Tally, follow this standard procedure:

1.  **Open Ledger:** Go to the specific input ledger (e.g., *Input CGST* or *Input SGST*).
2.  **Columnar View:** Press `F8` (Columnar) and ensure the following options are set to **"Yes"**:
    * Show Party's Name
    * Show Voucher Type
    * Show Voucher Number
    * Show Supplier Invoice/Reference Number
    * Show Party's GSTIN/UIN
3.  **Export:** Export the report to Excel.
4.  **Clean the Data:**
    * **Remove Journals:** Delete any "Journal" voucher rows; keep only "Purchase" entries.
    * **Fix Negative Values:** Tally often exports Taxable Values as negative numbers (Credit balance). Convert these to **positive numbers** (e.g., use the `=ABS()` formula or multiply by -1).
    * **Final Check:** Ensure your file has headers in the first row (GSTIN, Invoice No, Date, Value, Tax).

### 2️⃣ Preparing the GSTR-2B (from GST Portal)
1.  **Download:** Download the GSTR-2B Excel file from the GST Portal.
2.  **Isolate B2B Data:** Open the file and move the **"B2B"** sheet to a new Excel file (or keep it as the only active sheet).
3.  **Clean Headers (Crucial Step):**
    * The portal file usually has 4-5 rows of metadata at the top. **Delete these rows.**
    * Ensure the **Column Headers** are in **Row 1**.
    * **Unmerge Headers:** If "Invoice Details" is a merged header above specific columns, delete it.
    * **Standardize Names:** Ensure your headers look like this (single row):
        * `Invoice Number`, `Invoice Date`, `Invoice Value(₹)`
        * `Integrated Tax(₹)`, `Central Tax(₹)`, `State/UT Tax(₹)`
4.  **Save:** Save the clean file.

## How It Works
1.  **Browse** your Purchase Register Excel file.
2.  **Browse** your GSTR-2B Excel file.
3.  Click **Start Reconciliation**.
4.  The tool automatically generates a `Rekvia_Reconciliation_Report.xlsx` in the same folder.
  
## Understanding the Report

The output file `Rekvia_Reconciliation_Report.xlsx` contains the following status flags:

| Status | Meaning | Risk Level |
| :--- | :--- | :--- |
| **Matched** | Perfect match between Books and Portal. | 🟢 LOW |
| **Matched (Smart)** | Matched using logic (e.g., minor invoice spelling diff). | 🟢 LOW |
| **Mismatch in Value** | Invoice found, but Tax Amount differs > ₹2.00. | 🟡 MEDIUM |
| **Missing in GSTR-2B** | Invoice is in Books but NOT in Portal. (ITC Risk). | 🔴 HIGH |
| **Not in Books** | Invoice is in Portal but NOT in Books. (Unclaimed ITC). | ⚪ LOW |

### Privacy & Security
* **100% Offline Core:** The core file-processing engine operates locally on your machine. No financial or invoice data is ever uploaded to the cloud!
* **No Installation Needed:** Runs directly as a portable `.exe` file.

## Contact & Support
Developed by **Tamil Venthan**.

* [LinkedIn](https://www.linkedin.com/in/tamil-venthan4/)
* [Telegram](https://t.me/tamilventhan4)

---
*Note: This tool is for educational and professional aid purposes.*

*Disclaimer: This tool is provided as-is under the MIT License. While it is designed for accuracy, the developer is not liable for financial discrepancies. Always verify critical tax data.*
