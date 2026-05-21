"""
CSV parser for Saudi bank statements.
Supports: Al-Rajhi, Al-Ahli (NCB), Inma, Riyad Bank.
Handles: Arabic-Indic numerals, single amount column, Hijri dates,
         repeated headers, empty rows, summary rows.
"""

import io
import pandas as pd
from .cleaner import clean_transactions, normalize_numerals, normalize_amount


# ── Column aliases ────────────────────────────────────────────────────────────

DATE_COLS   = [
    'التاريخ', 'التاريخ الميلادي', 'Date', 'Transaction Date', 'Txn Date',
    'تاريخ', 'transaction date', 'date', 'txn date',
]
DESC_COLS   = [
    'البيان', 'Description', 'Narrative', 'Narration',
    'وصف العملية', 'التفاصيل', 'Transaction Details', 'Details',
    'بيان', 'narrative', 'description', 'narration', 'details',
    'transaction details',
]
DEBIT_COLS  = [
    'المدين', 'Withdrawal (SAR)', 'Withdrawal', 'Debit', 'Debit (SAR)',
    'مبلغ السحب', 'Amount Out', 'withdrawal', 'debit', 'debit (sar)',
    'amount out', 'withdrawal (sar)',
]
CREDIT_COLS = [
    'الدائن', 'Deposit (SAR)', 'Deposit', 'Credit', 'Credit (SAR)',
    'مبلغ الإيداع', 'Amount In', 'deposit', 'credit', 'credit (sar)',
    'amount in', 'deposit (sar)',
]
# Single-column amount (+/- sign distinguishes debit/credit)
AMOUNT_COLS = [
    'Amount (SAR)', 'Amount', 'المبلغ', 'مبلغ العملية',
    'amount (sar)', 'amount', 'المبلغ (ريال)',
]


def _find_col(df_cols: list, aliases: list) -> str | None:
    lower_map = {c.strip().lower(): c for c in df_cols}
    for alias in aliases:
        match = lower_map.get(alias.strip().lower())
        if match:
            return match
    return None


# ── CSV loading ───────────────────────────────────────────────────────────────

def _read_csv(raw: bytes) -> pd.DataFrame:
    """Decode and parse a CSV, tolerating encoding/formatting issues."""
    for encoding in ('utf-8-sig', 'utf-8', 'cp1256', 'iso-8859-6', 'cp1252'):
        try:
            content = raw.decode(encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        raise ValueError('Unable to decode CSV — unsupported encoding')

    # NOTE: Do NOT normalise Arabic-Indic numerals on the full content here —
    # that would turn Arabic thousands separators (٬) into ASCII commas (,)
    # and break the CSV field parsing. We normalise per-cell instead.

    try:
        df = pd.read_csv(
            io.StringIO(content),
            dtype=str,
            skip_blank_lines=True,
            on_bad_lines='skip',   # skip malformed rows silently
        )
    except Exception as e:
        raise ValueError(f'CSV parsing failed: {e}')

    df.columns = [c.strip() for c in df.columns]
    return df


def _drop_repeated_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows that are duplicates of the header (common in multi-page exports)."""
    header_vals = set(df.columns.str.strip().str.lower())
    mask = df.apply(
        lambda row: not any(
            str(v).strip().lower() in header_vals for v in row
        ),
        axis=1,
    )
    return df[mask].reset_index(drop=True)


# ── Main entry point ──────────────────────────────────────────────────────────

def parse_csv(file) -> list[dict]:
    """
    Parse a bank statement CSV and return normalised transaction dicts.
    """
    try:
        raw = file.read()
    except AttributeError:
        with open(file, 'rb') as f:
            raw = f.read()

    df = _read_csv(raw)
    df = _drop_repeated_headers(df)

    cols = df.columns.tolist()

    date_col   = _find_col(cols, DATE_COLS)
    desc_col   = _find_col(cols, DESC_COLS)
    debit_col  = _find_col(cols, DEBIT_COLS)
    credit_col = _find_col(cols, CREDIT_COLS)
    amount_col = _find_col(cols, AMOUNT_COLS)   # single-column format

    if not date_col or not desc_col:
        raise ValueError(
            f'Could not identify required columns. Found: {list(cols)}'
        )

    transactions = []
    for _, row in df.iterrows():
        # Normalise Arabic-Indic per cell (safe — doesn't break CSV structure)
        date_val = normalize_numerals(str(row[date_col])).strip()
        desc_val = str(row[desc_col]).strip()

        # Skip completely empty or NaN rows
        if not date_val or date_val.lower() in ('nan', '', 'none'):
            continue
        if not desc_val or desc_val.lower() in ('nan', '', 'none'):
            continue

        # Determine amount
        if amount_col:
            # Single-column: +12000.00 = credit, -125.50 = debit
            amount = normalize_amount(row.get(amount_col))
        else:
            debit  = normalize_amount(row.get(debit_col))  if debit_col  else 0.0
            credit = normalize_amount(row.get(credit_col)) if credit_col else 0.0

            if debit == 0.0 and credit == 0.0:
                continue   # no money movement

            amount = credit - debit if credit > 0 else -debit

        transactions.append({
            'date':          date_val,
            'merchant':      desc_val,
            'amount':        amount,
            'currency':      'SAR',
            'original_text': desc_val,
        })

    if not transactions:
        raise ValueError('No transactions found in the CSV file')

    return clean_transactions(transactions)
