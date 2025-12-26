# Rekvia
Python-based automation tool for GST Reconciliation

**Rekvia** is a powerful, automated desktop tool designed for finance professionals to reconcile Purchase Registers with GSTR-2B files instantly.

![Rekvia Status](https://img.shields.io/badge/Status-v1.0-brightgreen) ![Python](https://img.shields.io/badge/Built%20With-Python-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## Key Features

### Intelligent Matching Engine
* **Fuzzy Logic Matching:** Uses advanced algorithms to match invoices even if there are minor spelling differences (e.g., "TATA SONS" vs "TATA SONS LTD").
* **Smart Tolerance:** Automatically handles small tax differences (default tolerance: ±₹2.00) to avoid false mismatches.
* **Duplicate Prevention:** Ensures one-to-one matching so a single invoice isn't used twice.

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
* **100% Offline:** All processing happens locally on your machine. No financial data is uploaded to the cloud.
* **No Installation Needed:** Runs directly as a portable `.exe` file.

## Installation & Usage

### Option 1: Run the Executable (No Python Required)
1.  Go to the [Releases](https://github.com/Tamil-Venthan/Rekvia/releases) page.
2.  Download `Rekvia.exe`.
3.  Double-click to run.

### Option 2: Run from Source
1.  Clone the repository:
    ```bash
    git clone [https://github.com/Tamil-Venthan/Rekvia.git](https://github.com/Tamil-Venthan/Rekvia.git)
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the script:
    ```bash
    python rekvia.py
    ```

## How It Works
1.  **Browse** your Purchase Register Excel file.
2.  **Browse** your GSTR-2B Excel file.
3.  Click **Start Reconciliation**.
4.  The tool automatically generates a `Rekvia_Reconciliation_Report.xlsx` in the same folder.

## Contact & Support
Developed by **Tamil Venthan**.

* [LinkedIn](https://www.linkedin.com/in/tamil-venthan4/)
* [Telegram](https://t.me/tamilventhan4)

---
*Note: This tool is for educational and professional aid purposes.*

*Disclaimer: This tool is provided as-is under the MIT License. While it is designed for accuracy, the developer is not liable for financial discrepancies. Always verify critical tax data.*
