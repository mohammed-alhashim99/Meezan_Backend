"""
PDF parser for Saudi bank statements.
Strategy:
  1. pdfplumber table extraction   ← works on most digital PDFs
  2. pdfplumber text extraction    ← fallback for PDFs with no detected tables
  3. pytesseract OCR               ← last resort for scanned/image PDFs
"""

import io
import re
import pdfplumber
from .cleaner import clean_transactions, normalize_numerals, normalize_amount


# ── Column aliases (same as csv_parser, kept in one place) ──────────────────

DATE_ALIASES   = ['date', 'transaction date', 'txn date', 'التاريخ', 'تاريخ']
DESC_ALIASES   = ['description', 'narration', 'narrative', 'transaction details',
                  'details', 'البيان', 'وصف العملية', 'التفاصيل']
DEBIT_ALIASES  = ['debit', 'debit (sar)', 'withdrawal', 'amount out',
                  'المدين', 'سحب', 'مبلغ السحب']
CREDIT_ALIASES = ['credit', 'credit (sar)', 'deposit', 'amount in',
                  'الدائن', 'إيداع', 'مبلغ الإيداع']

# Regex to recognise a date-like cell (covers all 4 bank formats)
_DATE_RE = re.compile(
    r'^\d{2}[/\-\.]\d{2}[/\-\.]\d{2,4}$'   # DD/MM/YYYY  DD-MM-YYYY
    r'|\d{4}[/\-]\d{2}[/\-]\d{2}'           # YYYY-MM-DD  YYYY/MM/DD
    r'|\d{2}[- ][A-Za-z]{3}[- ]\d{2,4}'     # 15-Apr-26
)

# Regex for amount cells
_AMOUNT_RE = re.compile(r'^\d{1,3}(,\d{3})*(\.\d{2})?$')


def _norm(s: str) -> str:
    return s.strip().lower() if s else ''


def _match_col(headers: list[str], aliases: list[str]) -> int | None:
    """Return index of first header matching any alias, or None."""
    for i, h in enumerate(headers):
        if _norm(h) in [a.lower() for a in aliases]:
            return i
    return None


def _to_float(val: str) -> float:
    return normalize_amount(val)


# ── Strategy 1: table extraction ─────────────────────────────────────────────

def _parse_tables(pdf: pdfplumber.PDF) -> list[dict] | None:
    """Extract transactions from the first detected table across all pages."""
    raw = []
    col_map = None

    for page in pdf.pages:
        tables = page.extract_tables()
        if not tables:
            continue

        for table in tables:
            if not table or len(table) < 2:
                continue

            header_row = [str(c or '').strip() for c in table[0]]

            # Map columns on first encounter
            if col_map is None:
                date_i   = _match_col(header_row, DATE_ALIASES)
                desc_i   = _match_col(header_row, DESC_ALIASES)
                debit_i  = _match_col(header_row, DEBIT_ALIASES)
                credit_i = _match_col(header_row, CREDIT_ALIASES)

                if date_i is None or desc_i is None:
                    continue   # not a transaction table

                col_map = (date_i, desc_i, debit_i, credit_i)

            date_i, desc_i, debit_i, credit_i = col_map

            for row in table[1:]:
                cells = [str(c or '').strip() for c in row]
                if len(cells) <= max(date_i, desc_i):
                    continue

                date_val = cells[date_i]
                desc_val = cells[desc_i]

                if not date_val or not _DATE_RE.match(date_val):
                    continue   # skip non-data rows

                debit  = _to_float(cells[debit_i])  if debit_i  is not None and debit_i  < len(cells) else 0.0
                credit = _to_float(cells[credit_i]) if credit_i is not None and credit_i < len(cells) else 0.0
                amount = credit - debit if credit > 0 else -debit

                raw.append({
                    'date':          date_val,
                    'merchant':      desc_val,
                    'amount':        amount,
                    'currency':      'SAR',
                    'original_text': desc_val,
                })

    return raw if raw else None


# ── Strategy 2: raw text extraction ──────────────────────────────────────────

# Matches lines like: "15/04/2026   Hyper Panda Riyadh   125.50      11874.50"
_TEXT_ROW_RE = re.compile(
    r'(\d{2}[/\-\.]\d{2}[/\-\.]\d{2,4}|\d{4}[/\-]\d{2}[/\-]\d{2})'  # date
    r'\s+(.+?)\s+'                                                       # description
    r'(\d[\d,]*\.\d{2})'                                                # amount
    r'(?:\s+(\d[\d,]*\.\d{2}))?',                                       # optional balance
)


def _parse_text(pdf: pdfplumber.PDF) -> list[dict] | None:
    raw = []
    for page in pdf.pages:
        text = page.extract_text() or ''
        for line in text.splitlines():
            m = _TEXT_ROW_RE.search(line)
            if not m:
                continue
            date_val, desc_val, amount_str = m.group(1), m.group(2).strip(), m.group(3)
            raw.append({
                'date':          date_val,
                'merchant':      desc_val,
                'amount':        -_to_float(amount_str),  # assume expense if ambiguous
                'currency':      'SAR',
                'original_text': desc_val,
            })
    return raw if raw else None


# ── Strategy 3: OCR fallback ──────────────────────────────────────────────────

def _parse_ocr(pdf: pdfplumber.PDF) -> list[dict]:
    """Render each page as image, run Tesseract, then re-apply text strategy."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise RuntimeError('pytesseract / Pillow not installed — OCR unavailable')

    full_text_pages = []
    for page in pdf.pages:
        img = page.to_image(resolution=200).original
        text = pytesseract.image_to_string(img, lang='ara+eng')
        full_text_pages.append(text)

    # Reuse text strategy on OCR output
    raw = []
    for text in full_text_pages:
        for line in text.splitlines():
            m = _TEXT_ROW_RE.search(line)
            if not m:
                continue
            date_val, desc_val, amount_str = m.group(1), m.group(2).strip(), m.group(3)
            raw.append({
                'date':          date_val,
                'merchant':      desc_val,
                'amount':        -_to_float(amount_str),
                'currency':      'SAR',
                'original_text': desc_val,
            })

    if not raw:
        raise ValueError('OCR found no transaction data — unsupported PDF format')
    return raw


# ── Public entry point ────────────────────────────────────────────────────────

def parse_pdf(file) -> list[dict]:
    """
    Parse a bank statement PDF and return normalised transaction dicts.
    Tries table extraction → text extraction → OCR in order.
    """
    try:
        data = file.read()
    except AttributeError:
        with open(file, 'rb') as f:
            data = f.read()

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        # Strategy 1 — tables
        raw = _parse_tables(pdf)
        strategy = 'table'

        # Strategy 2 — raw text
        if not raw:
            raw = _parse_text(pdf)
            strategy = 'text'

        # Strategy 3 — OCR
        if not raw:
            raw = _parse_ocr(pdf)
            strategy = 'ocr'

    if not raw:
        raise ValueError('Could not extract any transactions from the PDF')

    result = clean_transactions(raw)
    # Attach parsing strategy for debugging (not in final response)
    for t in result:
        t['_strategy'] = strategy
    return result
