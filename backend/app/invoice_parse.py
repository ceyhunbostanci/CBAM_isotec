from pypdf import PdfReader
import re

def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    txt = ""
    for p in reader.pages:
        t = p.extract_text() or ""
        txt += "\n" + t
    return txt

def guess_energy_from_text(text: str):
    # Very lightweight heuristics (MVP). We will harden with supplier-specific parsers later.
    # Electricity: look for kWh patterns
    kwh = None
    m = re.search(r"(kWh)\s*[:=]?\s*([0-9][0-9\.,]*)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"([0-9][0-9\.,]*)\s*kWh", text, re.IGNORECASE)
    if m:
        num = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
        kwh = float(num.replace(".", "").replace(",", "."))
    # Natural gas: look for Sm3 / Nm3 / m3 patterns
    gas = None
    m2 = re.search(r"(Sm\s*3|Nm\s*3|m\s*3)\s*[:=]?\s*([0-9][0-9\.,]*)", text, re.IGNORECASE)
    if not m2:
        m2 = re.search(r"([0-9][0-9\.,]*)\s*(Sm\s*3|Nm\s*3|m\s*3)", text, re.IGNORECASE)
    if m2:
        num = m2.group(2) if m2.lastindex and m2.lastindex >= 2 else m2.group(1)
        gas = float(num.replace(".", "").replace(",", "."))
    return kwh, gas
