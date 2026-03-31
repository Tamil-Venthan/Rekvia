import json
import os
from typing import Dict, Any

import sys

if getattr(sys, 'frozen', False):
    # Running as executable
    base_dir = os.path.dirname(sys.executable)
else:
    # Running as script
    base_dir = os.path.dirname(__file__)

CONFIG_PATH = os.path.join(base_dir, 'settings.json')

DEFAULT_SETTINGS = {
    "BOOK_COLUMN_ALIASES": {
        "gstin": ["GSTIN/UIN", "GSTIN", "GST Number", "Supplier GSTIN", "Tin No", "Party GSTIN"],
        "inv_no": ["Voucher Ref. No.", "Invoice No", "Invoice Number", "Bill No", "Doc No", "Ref No"],
        "date": ["Voucher Ref. Date", "Invoice Date", "Bill Date", "Doc Date", "Date"],
        "tax_cgst": ["INPUT CGST", "CGST", "Central Tax", "CGST Amount", "CGST Amt"],
        "tax_sgst": ["INPUT SGST", "SGST", "State/UT Tax", "SGST Amount", "SGST Amt"],
        "tax_igst": ["INPUT IGST", "IGST", "Integrated Tax", "IGST Amount", "IGST Amt"],
        "value": ["Value", "Taxable Value", "Taxable Amount", "Gross Value", "Net Amount"],
        "vendor": ["Buyer/Supplier", "Party Name", "Supplier Name", "Vendor Name", "Trade Name", "Particulars"]
    },
    "GSTR2B_COLUMN_ALIASES": {
        "gstin": ["GSTIN of supplier", "GSTIN", "Supplier GSTIN"],
        "inv_no": ["Invoice number", "Invoice No", "Inv No"],
        "date": ["Invoice Date", "Inv Date", "Date"],
        "tax_cgst": ["Central Tax(₹)", "Central Tax", "CGST", "CGST(₹)"],
        "tax_sgst": ["State/UT Tax(₹)", "State/UT Tax", "SGST", "SGST(₹)"],
        "tax_igst": ["Integrated Tax(₹)", "Integrated Tax", "IGST", "IGST(₹)"],
        "value": ["Taxable Value (₹)", "Taxable Value", "Taxable Amt"],
        "vendor": ["Trade/Legal name", "Trade Name", "Legal Name", "Name"],
        "itc": ["ITC Availability", "ITC Available", "Eligibility for ITC", "ITC Status"],
        "rcm": ["Reverse Charge", "RCM", "Reverse Charge Mechanism"]
    },
    "TOLERANCE": 2.0,
    "CONTACT_LINKS": {
        "telegram": "https://t.me/tamilventhan4",
        "linkedin": "https://www.linkedin.com/in/tamil-venthan4/",
        "github": "https://github.com/Tamil-Venthan"
    }
}

APP_VERSION = "v1.2.0"

def load_settings() -> Dict[str, Any]:
    """Loads configuration from settings.json or returns default values."""
    if not os.path.exists(CONFIG_PATH):
        # Fallback to defaults to avoid empty UI for compiled EXE
        return DEFAULT_SETTINGS
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure critical keys exist even if user corrupted the json
            for key in ["BOOK_COLUMN_ALIASES", "GSTR2B_COLUMN_ALIASES", "CONTACT_LINKS"]:
                if key not in data:
                    data[key] = DEFAULT_SETTINGS[key]
            return data
    except Exception:
        return DEFAULT_SETTINGS

# Load once on module import
SETTINGS = load_settings()
BOOK_COLUMN_ALIASES = SETTINGS.get("BOOK_COLUMN_ALIASES", {})
GSTR2B_COLUMN_ALIASES = SETTINGS.get("GSTR2B_COLUMN_ALIASES", {})
TOLERANCE = SETTINGS.get("TOLERANCE", 2.0)
CONTACT_LINKS = SETTINGS.get("CONTACT_LINKS", {})

def save_settings(new_settings: Dict[str, Any]):
    """Saves configuration back to settings.json."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_settings, f, indent=4)

