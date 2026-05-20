"""
Transaction cleaner — normalises dates and merchant names.
Works on the output of both csv_parser and pdf_parser.
"""

import re
from datetime import datetime


# ── Date parsing ──────────────────────────────────────────────────────────────

DATE_FORMATS = [
    '%d/%m/%Y',      # 15/04/2026  (Al-Rajhi AR)
    '%Y-%m-%d',      # 2026-04-15  (Ahli EN)
    '%d-%b-%y',      # 15-Apr-26   (Inma)
    '%d-%b-%Y',      # 15-Apr-2026
    '%Y/%m/%d',      # 2026/04/15  (Riyad)
    '%m/%d/%Y',      # 04/15/2026  (US format fallback)
    '%d.%m.%Y',      # 15.04.2026
]

ARABIC_MONTHS = {
    'يناير': 'January',   'فبراير': 'February', 'مارس': 'March',
    'أبريل': 'April',     'ابريل': 'April',      'مايو': 'May',
    'يونيو': 'June',      'يوليو': 'July',       'أغسطس': 'August',
    'سبتمبر': 'September','أكتوبر': 'October',   'نوفمبر': 'November',
    'ديسمبر': 'December',
}


def _parse_date(raw: str) -> str:
    """Return YYYY-MM-DD string from any recognised date format."""
    raw = raw.strip()

    # Replace Arabic month names
    for ar, en in ARABIC_MONTHS.items():
        raw = raw.replace(ar, en)

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Last resort: let pandas try
    try:
        import pandas as pd
        return pd.to_datetime(raw, dayfirst=True).strftime('%Y-%m-%d')
    except Exception:
        return raw   # return as-is so we don't silently drop the row


# ── Merchant cleaning ─────────────────────────────────────────────────────────

# Noise prefixes common in Saudi bank statements
_NOISE = re.compile(
    r'^(شراء\s*POS\s*|مشتريات\s*|POS\s*PURCHASE\s*|POS\s*|'
    r'فاتورة\s*|BILL\s*PAYMENT\s*|BILL\s*PMT\s*|'
    r'تحويل\s*(إلى|لـ|الى)?\s*|TRF\s*(TO\s*)?|'
    r'إيداع\s*|SALARY\s*|إيداع\s*راتب\s*)',
    re.IGNORECASE,
)

# Trailing noise: city names and codes that aren't merchant names
_TRAILING = re.compile(
    r'\s+(الرياض|جده|جدة|الدمام|RIYADH|JEDDAH|DAMMAM|KSA|\d{3,})\s*$',
    re.IGNORECASE,
)

# Month/year noise left after prefix stripping (e.g. "APRIL 2026", "APR 2026")
_MONTH_YEAR = re.compile(
    r'^(january|february|march|april|may|june|july|august|september|'
    r'october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)'
    r'(\s+\d{2,4})?$',
    re.IGNORECASE,
)


def _clean_merchant(raw: str) -> str:
    """Strip noise prefixes/suffixes to get a clean merchant name."""
    name = _NOISE.sub('', raw).strip()
    name = _TRAILING.sub('', name).strip()
    # If we over-cleaned and what's left is just a month/year, keep original
    if _MONTH_YEAR.match(name):
        return raw.strip()
    return name if name else raw


# ── Main entry point ──────────────────────────────────────────────────────────

def clean_transactions(raw: list[dict]) -> list[dict]:
    """
    Normalise a list of raw transaction dicts.
    Input keys:  date, merchant, amount, currency, original_text
    Output adds: date (YYYY-MM-DD), merchant (cleaned)
    """
    cleaned = []
    for t in raw:
        try:
            cleaned.append({
                'date':          _parse_date(t['date']),
                'merchant':      _clean_merchant(t['merchant']),
                'amount':        round(float(t['amount']), 2),
                'currency':      t.get('currency', 'SAR'),
                'original_text': t.get('original_text', t['merchant']),
                'category':      t.get('category', ''),
                'category_ar':   t.get('category_ar', ''),
                'user_corrected': False,
            })
        except Exception:
            # Never silently crash on a single row — skip it
            continue
    return cleaned
