import pytest
from rekvia.core.utils import safe_float, normalize, validate_gstin, smart_invoice_match

def test_safe_float():
    assert safe_float("125,000.50") == 125000.50
    assert safe_float("NIL") == 0.0
    assert safe_float("-") == 0.0
    assert safe_float("abc") == 0.0
    assert safe_float(None) == 0.0
    
    # Test accounting formats
    assert safe_float("(1,250.00)") == -1250.00
    assert safe_float("-1,250.00") == -1250.00

def test_normalize():
    assert normalize("INV/2023/001") == "INV2023001"
    assert normalize(" Tata Sons Ltd. ") == "TATASONSLTD"

def test_validate_gstin():
    assert validate_gstin("27ABCDE1234F1Z5") == True
    assert validate_gstin("INVALID") == False
    assert validate_gstin(None) == False

def test_smart_invoice_match():
    # Exact match
    assert smart_invoice_match("INV-001", "INV/001") == True
    
    # Matching with/without year 2023/2024
    assert smart_invoice_match("AB/2024/056", "AB-056") == True
    assert smart_invoice_match("123", "123") == True

    # Completely different
    assert smart_invoice_match("INV-100", "INV-200") == False
