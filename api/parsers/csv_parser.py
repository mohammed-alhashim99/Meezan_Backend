"""
CSV parser for Saudi bank statements.
Supports: Al-Rajhi, Al-Ahli (NCB), Inma, Riyad Bank.
Returns a normalised list of transaction dicts regardless of source format.
"""

import io
import pandas as pd
from .cleaner import clean_transactions


# ── Column aliases ────────────────────────────────────────────────────────────

DATE_COLS    = ['التاريخ', 'Date', 'Transaction Date', 'تاريخ', 'transaction date', 'date']
DESC_COLS    = ['البيان', 'Description', 'Narrative', 'وصف العملية', 'بيان', 'narrative', 'description']
DEBIT_COLS   = ['المدين', 'Withdrawal (SAR)', 'Debit', 'مبلغ السحب', 'withdrawal', 'debit', 'سحب']
CREDIT_COLS  = ['الدائن', 'Deposit (SAR)', 'Credit', 'مبلغ الإيداع', 'deposit', 'credit', 'إيداع']


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_col(df_cols: list, aliases: list) -> str | None:
    """Return the first column name from df that matches any alias (case-insensitive)."""
    lower_map = {c.strip().lower(): c for c in df_cols}
    for alias in aliases:
        match = lower_map.get(alias.strip().lower())
        if match:
            return match
    return None


def _to_float(val) -> float:
    """Convert a cell value to float, return 0.0 on failure."""
    if pd.isna(val) or str(val).strip() in ('', '-', 'None'):
        return 0.0
    cleaned = str(val).replace(',', '').replace('٬', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


# ── Main entry point ──────────────────────────────────────────────────────────

def parse_csv(file) -> list[dict]:
    """
    Parse a bank statement CSV and return normalised transaction dicts.

    Each dict has:
        date          str   YYYY-MM-DD
        merchant      str   raw description text
        amount        float negative = expense, positive = income
        currency      str   'SAR'
        original_text str   raw description (unchanged)
    """
    # Read file — try UTF-8 first then cp1256 (common for Arabic CSVs)
    try:
        raw = file.read()
    except AttributeError:
        with open(file, 'rb') as f:
            raw = f.read()

    for encoding in ('utf-8-sig', 'utf-8', 'cp1256', 'iso-8859-6'):
        try:
            content = raw.decode(encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        raise ValueError('Unable to decode CSV — unsupported encoding')

    df = pd.read_csv(io.StringIO(content), dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # Locate columns
    date_col   = _find_col(df.columns.tolist(), DATE_COLS)
    desc_col   = _find_col(df.columns.tolist(), DESC_COLS)
    debit_col  = _find_col(df.columns.tolist(), DEBIT_COLS)
    credit_col = _find_col(df.columns.tolist(), CREDIT_COLS)

    if not date_col or not desc_col:
        raise ValueError(
            f'Could not identify required columns. Found: {list(df.columns)}'
        )

    transactions = []
    for _, row in df.iterrows():
        debit  = _to_float(row.get(debit_col))  if debit_col  else 0.0
        credit = _to_float(row.get(credit_col)) if credit_col else 0.0

        # Skip rows with no money movement (header repetitions, empty rows)
        if debit == 0.0 and credit == 0.0:
            continue

        # amount: negative for expenses, positive for income/deposits
        amount = credit - debit if credit > 0 else -debit

        transactions.append({
            'date':          str(row[date_col]).strip(),
            'merchant':      str(row[desc_col]).strip(),
            'amount':        amount,
            'currency':      'SAR',
            'original_text': str(row[desc_col]).strip(),
        })

    if not transactions:
        raise ValueError('No transactions found in the CSV file')

    return clean_transactions(transactions)
