"""
Transaction cleaner — normalises dates, amounts, and merchant names.
Works on the output of both csv_parser and pdf_parser.
"""

import re
from datetime import datetime


# ── Arabic-Indic numeral normalisation ───────────────────────────────────────

_INDIC_MAP = str.maketrans('٠١٢٣٤٥٦٧٨٩٫٬', '0123456789.,')


def normalize_numerals(s: str) -> str:
    """Convert Arabic-Indic digits and separators to ASCII equivalents."""
    return s.translate(_INDIC_MAP) if s else s


# ── Date parsing ──────────────────────────────────────────────────────────────

DATE_FORMATS = [
    '%d/%m/%Y',      # 15/04/2026  (Al-Rajhi AR)
    '%Y-%m-%d',      # 2026-04-15  (Ahli EN)
    '%d-%b-%y',      # 15-Apr-26   (Inma)
    '%d-%b-%Y',      # 15-Apr-2026
    '%d %b %y',      # 15 Apr 26   (Standard Chartered / Indian banks)
    '%d %b %Y',      # 15 Apr 2026
    '%Y/%m/%d',      # 2026/04/15  (Riyad)
    '%m/%d/%Y',      # 04/15/2026  (US format fallback)
    '%d.%m.%Y',      # 15.04.2026
    '%d-%m-%Y',      # 15-04-2026
]

ARABIC_MONTHS = {
    'يناير': 'January',   'فبراير': 'February', 'مارس': 'March',
    'أبريل': 'April',     'ابريل': 'April',      'مايو': 'May',
    'يونيو': 'June',      'يوليو': 'July',       'أغسطس': 'August',
    'سبتمبر': 'September','أكتوبر': 'October',   'نوفمبر': 'November',
    'ديسمبر': 'December',
}

# Hijri year range (roughly 1440–1450 AH = 2019–2029 CE)
_HIJRI_RE = re.compile(r'\b1[34]\d{2}\b')


def _hijri_to_gregorian(raw: str) -> str:
    """
    Rough Hijri → Gregorian conversion.
    Uses the approximation: G_year ≈ H_year * (365.25/354.37) + 622
    Accurate to ±1 day for most practical purposes.
    """
    # Try DD/MM/YYYY where YYYY is Hijri
    m = re.match(r'^(\d{1,2})[/\-](\d{1,2})[/\-](1[34]\d{2})$', raw)
    if m:
        d, mo, h_year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        g_year = int(h_year * (365.25 / 354.37) + 622)
        try:
            return datetime(g_year, mo, d).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return raw


def _parse_date(raw: str) -> str:
    """Return YYYY-MM-DD string from any recognised date format."""
    raw = normalize_numerals(raw.strip())

    # Replace Arabic month names with English equivalents
    for ar, en in ARABIC_MONTHS.items():
        raw = raw.replace(ar, en)

    # Try standard formats
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Try Hijri conversion if year looks Hijri
    if _HIJRI_RE.search(raw):
        converted = _hijri_to_gregorian(raw)
        if converted != raw:
            return converted

    # Last resort: pandas
    try:
        import pandas as pd
        return pd.to_datetime(raw, dayfirst=True).strftime('%Y-%m-%d')
    except Exception:
        return raw   # keep as-is — never drop a row over a date format


# ── Merchant cleaning ─────────────────────────────────────────────────────────

_NOISE = re.compile(
    r'^(شراء\s*POS\s*|مشتريات\s*|POS\s*PURCHASE\s*|POS\s*|'
    r'فاتورة\s*|BILL\s*PAYMENT\s*|BILL\s*PMT\s*|BILL\s*|'
    r'تحويل\s*(إلى|لـ|الى)?\s*|TRF\s*(TO\s*)?|TRANSFER\s*(TO\s*)?|'
    r'إيداع\s*راتب\s*|إيداع\s*|SALARY\s*)',
    re.IGNORECASE,
)

_TRAILING = re.compile(
    r'\s+(الرياض|جده|جدة|الدمام|مكة|المدينة|'
    r'RIYADH|JEDDAH|DAMMAM|MAKKAH|MEDINA|KSA|SA|\d{3,})\s*$',
    re.IGNORECASE,
)

_MONTH_YEAR = re.compile(
    r'^(january|february|march|april|may|june|july|august|september|'
    r'october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)'
    r'(\s+\d{2,4})?$',
    re.IGNORECASE,
)

# Summary/total rows to skip
_SUMMARY_ROW = re.compile(
    r'^(مجموع|إجمالي|total|subtotal|balance\s+b/?f|balance\s+forward|رصيد)',
    re.IGNORECASE,
)


def _clean_merchant(raw: str) -> str:
    if _SUMMARY_ROW.match(raw.strip()):
        return ''   # signal to skip this row
    name = _NOISE.sub('', raw).strip()
    name = _TRAILING.sub('', name).strip()
    if _MONTH_YEAR.match(name):
        return raw.strip()
    return name if name else raw


# ── Amount normalisation ──────────────────────────────────────────────────────

def normalize_amount(val) -> float:
    """Convert any amount representation to a float."""
    if val is None:
        return 0.0
    s = normalize_numerals(str(val)).strip()
    # Empty / pandas NaN string
    if s.lower() in ('', 'nan', 'none', '-', 'n/a'):
        return 0.0
    s = s.replace(' ', '').replace('SAR', '').replace('ر.س', '')
    # Remove thousands separators (comma after normalisation)
    # but keep minus sign and decimal point
    s = re.sub(r',(?=\d{3})', '', s)  # 12,000.00 → 12000.00
    s = s.replace(',', '')            # any remaining commas
    # Handle parenthesis negatives: (125.50) → -125.50
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


# ── Main entry point ──────────────────────────────────────────────────────────

def clean_transactions(raw: list[dict]) -> list[dict]:
    """
    Normalise a list of raw transaction dicts.
    Input keys:  date, merchant, amount, currency, original_text
    Output adds: date (YYYY-MM-DD), merchant (cleaned), amount (float)
    """
    cleaned = []
    for t in raw:
        try:
            merchant = _clean_merchant(t['merchant'])
            if not merchant:           # summary/total row — skip
                continue

            cleaned.append({
                'date':           _parse_date(t['date']),
                'merchant':       merchant,
                'amount':         round(normalize_amount(t['amount']), 2),
                'currency':       t.get('currency', 'SAR'),
                'original_text':  t.get('original_text', t['merchant']),
                'category':       t.get('category', ''),
                'category_ar':    t.get('category_ar', ''),
                'user_corrected': False,
            })
        except Exception:
            continue
    return cleaned
