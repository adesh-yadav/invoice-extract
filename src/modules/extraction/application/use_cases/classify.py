"""Conservative scope gate. Ambiguous documents go to review."""
from __future__ import annotations
import re
from src.modules.extraction.domain.cdr import CDR


def classify(cdr: CDR) -> str:
    text = cdr.ordered_text().lower()
    if not text.strip():
        return "unknown"
    if re.search(r"\b(pan card|aadhaar|passport|resume|curriculum vitae|purchase order|quotation)\b", text):
        return "unsupported"
    # PAN cards often print the full heading rather than the words "PAN card".
    # Require an identity-card field as well, since invoices may print a seller PAN.
    if re.search(r"\bpermanent account number\b", text) and re.search(r"\b(father['’]?s name|date of birth|director of income tax)\b", text):
        return "unsupported"
    if re.search(r"\b(tax invoice|invoice no|invoice number|invoice)\b", text):
        return "invoice"
    if re.search(r"\b(receipt|payment received|paid on)\b", text):
        return "receipt"
    if re.search(r"\b(bill|amount due|payable by)\b", text):
        return "bill"
    return "unknown"
