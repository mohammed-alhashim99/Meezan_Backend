"""
Generate 4 sample bank statement PDFs for testing the PDF parser.
Each bank has a slightly different table structure/layout.
Run once: python tests/create_test_pdfs.py
"""

import os, sys
sys.stdout.reconfigure(encoding='utf-8')

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = os.path.join(os.path.dirname(__file__))

# Register Arial for Arabic support
pdfmetrics.registerFont(TTFont('Arial', r'C:\Windows\Fonts\arial.ttf'))

TRANSACTIONS = [
    ('15/04/2026', 'Salary April 2026',          '',       '12000.00', '12000.00'),
    ('16/04/2026', 'Hyper Panda Riyadh',          '125.50', '',         '11874.50'),
    ('17/04/2026', 'Al-Baik Restaurant',          '45.00',  '',         '11829.50'),
    ('18/04/2026', 'Starbucks Riyadh',            '28.00',  '',         '11801.50'),
    ('19/04/2026', 'Transfer - Ahmed Al-Omar',    '500.00', '',         '11301.50'),
    ('20/04/2026', 'Careem Ride',                 '22.00',  '',         '11279.50'),
    ('21/04/2026', 'Al-Nahdi Pharmacy',           '87.00',  '',         '11192.50'),
    ('22/04/2026', 'STC Bill Payment',            '149.00', '',         '11043.50'),
    ('23/04/2026', 'Netflix Subscription',        '49.00',  '',         '10994.50'),
    ('24/04/2026', 'McDonalds Riyadh',            '38.50',  '',         '10956.00'),
    ('25/04/2026', 'Lulu Hypermarket',            '210.00', '',         '10746.00'),
    ('26/04/2026', 'Uber Trip',                   '35.00',  '',         '10711.00'),
    ('27/04/2026', 'Saudi Electricity Company',   '320.00', '',         '10391.00'),
    ('28/04/2026', 'Spotify Subscription',        '19.99',  '',         '10371.01'),
    ('29/04/2026', 'Tamimi Markets Riyadh',       '176.00', '',         '10195.01'),
    ('30/04/2026', 'Al-Dawa Pharmacy',            '55.00',  '',         '10140.01'),
    ('01/05/2026', 'Zara Riyadh',                 '349.00', '',         '9791.01'),
    ('02/05/2026', 'Riyadh Bus Authority',        '15.00',  '',         '9776.01'),
    ('03/05/2026', 'IKEA Riyadh',                 '520.00', '',         '9256.01'),
    ('04/05/2026', 'Leean Supermarket',           '95.00',  '',         '9161.01'),
    ('05/05/2026', 'Transfer - Saad Al-Qahtani',  '1000.00','',         '8161.01'),
    ('06/05/2026', 'Bait Al-Kabsa Restaurant',    '62.00',  '',         '8099.01'),
    ('07/05/2026', 'Mobily Bill',                 '199.00', '',         '7900.01'),
    ('08/05/2026', 'Amazon Saudi Arabia',         '450.00', '',         '7450.01'),
    ('09/05/2026', 'Jarir Bookstore',             '275.00', '',         '7175.01'),
    ('10/05/2026', 'Dunkin Donuts',               '32.00',  '',         '7143.01'),
]

STYLE = TableStyle([
    ('BACKGROUND',  (0,0), (-1,0),  colors.HexColor('#1a6b5a')),
    ('TEXTCOLOR',   (0,0), (-1,0),  colors.white),
    ('FONTNAME',    (0,0), (-1,-1), 'Arial'),
    ('FONTSIZE',    (0,0), (-1,0),  9),
    ('FONTSIZE',    (0,1), (-1,-1), 8),
    ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f7fa')]),
    ('GRID',        (0,0), (-1,-1), 0.3, colors.HexColor('#e5e7eb')),
    ('TOPPADDING',  (0,0), (-1,-1), 4),
    ('BOTTOMPADDING',(0,0),(-1,-1), 4),
])


def _make_pdf(filename, bank_name, headers, colwidths, rows):
    path = os.path.join(OUT, filename)
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', fontName='Arial', fontSize=14,
                                 textColor=colors.HexColor('#1a6b5a'),
                                 spaceAfter=6)
    sub_style   = ParagraphStyle('sub', fontName='Arial', fontSize=9,
                                 textColor=colors.HexColor('#6b7280'),
                                 spaceAfter=16)

    data = [headers] + rows
    tbl  = Table(data, colWidths=colwidths)
    tbl.setStyle(STYLE)

    story = [
        Paragraph(bank_name, title_style),
        Paragraph('Account Statement  |  Period: April - May 2026', sub_style),
        tbl,
    ]
    doc.build(story)
    print(f'Created: {path}')


# ── Al-Rajhi: Date | Description | Debit | Credit | Balance ────────────────
_make_pdf(
    'sample_alrajhi.pdf',
    'Al Rajhi Bank - Account Statement',
    ['Date', 'Description', 'Debit (SAR)', 'Credit (SAR)', 'Balance (SAR)'],
    [3*cm, 7.5*cm, 3*cm, 3*cm, 3*cm],
    [list(r) for r in TRANSACTIONS],
)

# ── Al-Ahli: Date | Narration | Withdrawal | Deposit | Balance ────────────
_make_pdf(
    'sample_ahli.pdf',
    'National Commercial Bank (Ahli) - Statement',
    ['Txn Date', 'Narration', 'Withdrawal', 'Deposit', 'Balance'],
    [3*cm, 7.5*cm, 3*cm, 3*cm, 3*cm],
    [list(r) for r in TRANSACTIONS],
)

# ── Inma: Transaction Date | Narrative | Debit | Credit | Running Balance ──
_make_pdf(
    'sample_inma.pdf',
    'Bank Inma - Account Statement',
    ['Transaction Date', 'Narrative', 'Debit', 'Credit', 'Running Balance'],
    [3.5*cm, 7*cm, 3*cm, 3*cm, 3*cm],
    [list(r) for r in TRANSACTIONS],
)

# ── Riyad Bank: Date | Details | Amount Out | Amount In | Balance ──────────
_make_pdf(
    'sample_riyad.pdf',
    'Riyad Bank - Account Statement',
    ['Date', 'Transaction Details', 'Amount Out', 'Amount In', 'Balance'],
    [3*cm, 7.5*cm, 3*cm, 3*cm, 3*cm],
    [list(r) for r in TRANSACTIONS],
)

print('\nAll 4 PDFs created successfully.')
