"""
Bank PDF Checker — run on any new bank statement to see if the parser handles it.

Usage:
    python tests/check_bank.py "path/to/statement.pdf"

Output:
    - Which strategy worked (table / text / anb_text / ocr / FAILED)
    - How many transactions extracted
    - First 5 transactions preview
    - If it FAILED: shows raw table headers and text lines to help diagnose
"""

import sys
import os
import io
import pdfplumber
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from api.parsers.pdf_parser import (
    parse_pdf, _parse_tables, _parse_text, _parse_anb_text,
    DATE_ALIASES, DESC_ALIASES, DEBIT_ALIASES, CREDIT_ALIASES, _match_col,
)
from api.parsers.cleaner import clean_transactions

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
RESET  = '\033[0m'
BOLD   = '\033[1m'


def _nfkc(s: str) -> str:
    return unicodedata.normalize('NFKC', s or '').strip()


def _section(title: str):
    print(f'\n{CYAN}{BOLD}{"─"*60}{RESET}')
    print(f'{CYAN}{BOLD}  {title}{RESET}')
    print(f'{CYAN}{"─"*60}{RESET}')


def check(path: str):
    if not os.path.exists(path):
        print(f'{RED}File not found: {path}{RESET}')
        sys.exit(1)

    name = os.path.basename(path)
    print(f'\n{BOLD}Bank PDF Checker{RESET}')
    print(f'File : {name}')
    print(f'Size : {os.path.getsize(path) / 1024:.1f} KB')

    # ── Try the full parser ───────────────────────────────────────────────────
    _section('Parser result')
    try:
        result = parse_pdf(path)
        strategy = result[0]['_strategy'] if result else 'none'
        n = len(result)
        print(f'{GREEN}✓ PASS{RESET}  {n} transactions extracted   [strategy: {strategy}]')
        print()
        # Show first 5
        for t in result[:5]:
            sign = '+' if t['amount'] >= 0 else ''
            print(f'  {t["date"]}  {sign}{t["amount"]:>10.2f}  {t["merchant"][:50]}')
        if n > 5:
            print(f'  ... and {n - 5} more')

        # Basic quality checks
        print()
        has_debit  = any(t['amount'] < 0 for t in result)
        has_credit = any(t['amount'] > 0 for t in result)
        zero_amt   = sum(1 for t in result if t['amount'] == 0)
        bad_merch  = sum(1 for t in result
                         if t['merchant'].replace('.', '').replace(',', '').strip().isnumeric())

        checks = [
            (has_debit,          'Has debit (negative) transactions'),
            (has_credit,         'Has credit (positive) transactions'),
            (zero_amt == 0,      f'No zero-amount rows  ({zero_amt} found)'),
            (bad_merch == 0,     f'No amounts-as-merchants  ({bad_merch} found)'),
        ]
        for ok, label in checks:
            icon = f'{GREEN}✓{RESET}' if ok else f'{YELLOW}⚠{RESET}'
            print(f'  {icon}  {label}')

        if not has_debit or not has_credit or zero_amt > 0 or bad_merch > 0:
            print(f'\n{YELLOW}Parser ran but data quality issues detected — '
                  f'see diagnostics below.{RESET}')
            _show_diagnostics(path)

        return True

    except Exception as e:
        print(f'{RED}✗ FAILED{RESET}  {e}')
        _show_diagnostics(path)
        return False


def _show_diagnostics(path: str):
    """Show raw table headers and text lines to help diagnose parsing issues."""
    with open(path, 'rb') as f:
        data = f.read()

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        _section('Diagnostics: table headers found')
        found_any = False
        for pi, page in enumerate(pdf.pages[:3]):
            tables = page.extract_tables()
            for ti, table in enumerate(tables or []):
                if not table:
                    continue
                # Show first 4 rows of each table
                for ri, row in enumerate(table[:4]):
                    cells = [_nfkc(str(c or ''))[:40] for c in row]
                    # Check if this row looks like a header
                    date_match = _match_col(cells, DATE_ALIASES)
                    desc_match = _match_col(cells, DESC_ALIASES)
                    debit_match = _match_col(cells, DEBIT_ALIASES)
                    credit_match = _match_col(cells, CREDIT_ALIASES)
                    is_header = date_match is not None and desc_match is not None
                    tag = f'{GREEN}[HEADER DETECTED]{RESET}' if is_header else ''
                    if ri == 0:
                        print(f'\n  Page {pi+1}, Table {ti+1}:')
                    print(f'    row{ri}: {cells} {tag}')
                    if is_header:
                        found_any = True
                        print(f'    {GREEN}→ date_col={date_match}  desc_col={desc_match}  '
                              f'debit_col={debit_match}  credit_col={credit_match}{RESET}')

        if not found_any:
            print(f'  {YELLOW}No recognisable header row found in first 3 pages.{RESET}')
            print(f'  {YELLOW}Known date aliases:   {DATE_ALIASES[:6]}...{RESET}')
            print(f'  {YELLOW}Known desc aliases:   {DESC_ALIASES[:6]}...{RESET}')
            print(f'  {YELLOW}Known debit aliases:  {DEBIT_ALIASES}{RESET}')
            print(f'  {YELLOW}Known credit aliases: {CREDIT_ALIASES}{RESET}')

        _section('Diagnostics: text lines (page 1, first 30 lines)')
        text = pdf.pages[0].extract_text() or ''
        for i, ln in enumerate(text.splitlines()[:30]):
            print(f'  {i:02d}: {repr(_nfkc(ln)[:100])}')

    _section('What to do next')
    print('  1. Look at the table header row above.')
    print('  2. If a header was found but columns are wrong — add missing')
    print('     column aliases to DATE_ALIASES / DESC_ALIASES / DEBIT_ALIASES')
    print('     / CREDIT_ALIASES in api/parsers/pdf_parser.py')
    print('  3. If NO header was found — the bank may use a text-only layout.')
    print('     Check if lines follow: "DATE  description  amount  balance"')
    print('  4. Share the PDF with Claude — paste the diagnostics output above.')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tests/check_bank.py "path/to/statement.pdf"')
        print()
        print('Example:')
        print('  python tests/check_bank.py "C:/Downloads/statement.pdf"')
        sys.exit(1)

    success = check(sys.argv[1])
    sys.exit(0 if success else 1)
