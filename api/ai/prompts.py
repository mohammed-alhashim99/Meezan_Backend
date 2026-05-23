"""
Fixed categories, Saudi merchant dictionary, and Claude prompt templates.
"""

# ── The 8 fixed categories ────────────────────────────────────────────────────

CATEGORIES = [
    'Food & Dining',
    'Transport',
    'Shopping',
    'Bills & Utilities',
    'Health',
    'Entertainment',
    'Transfers',
    'Other',
]

CATEGORIES_AR = {
    'Food & Dining':    'طعام ومطاعم',
    'Transport':        'مواصلات',
    'Shopping':         'تسوق',
    'Bills & Utilities':'فواتير',
    'Health':           'صحة',
    'Entertainment':    'ترفيه',
    'Transfers':        'تحويلات',
    'Other':            'أخرى',
}

# ── Saudi merchant dictionary ─────────────────────────────────────────────────
# Pre-classify ~60 well-known Saudi merchants to save API calls & improve accuracy.
# Keys are lowercase substrings; first match wins.

MERCHANT_DICT: dict[str, str] = {
    # Food & Dining
    'هايبر باندا':      'Food & Dining',
    'hyper panda':      'Food & Dining',
    'البيك':            'Food & Dining',
    'albaik':           'Food & Dining',
    'al-baik':          'Food & Dining',
    'al baik':          'Food & Dining',
    'ماكدونالدز':       'Food & Dining',
    'mcdonald':         'Food & Dining',
    'برغر كنج':         'Food & Dining',
    'burger king':      'Food & Dining',
    'كنتاكي':           'Food & Dining',
    'kfc':              'Food & Dining',
    'ستاربكس':          'Food & Dining',
    'starbucks':        'Food & Dining',
    'كوستا':            'Food & Dining',
    'costa coffee':     'Food & Dining',
    'tim horton':       'Food & Dining',
    'دانكن':            'Food & Dining',
    'dunkin':           'Food & Dining',
    'تميمي':            'Food & Dining',
    'tamimi':           'Food & Dining',
    'بنده':             'Food & Dining',
    'bindawood':        'Food & Dining',
    'بيت الكبسة':       'Food & Dining',
    'bait alkabsa':     'Food & Dining',
    'لولو':             'Food & Dining',
    'lulu':             'Food & Dining',
    'ليان':             'Food & Dining',
    'leean':            'Food & Dining',
    'باسكن روبنز':      'Food & Dining',
    'baskin':           'Food & Dining',
    'سبواي':            'Food & Dining',
    'subway':           'Food & Dining',
    'بيتزا هت':         'Food & Dining',
    'pizza hut':        'Food & Dining',
    'دومينوز':          'Food & Dining',
    'domino':           'Food & Dining',
    # Transport
    'كريم':             'Transport',
    'careem':           'Transport',
    'اوبر':             'Transport',
    'uber':             'Transport',
    'تكسي':             'Transport',
    'حافلات الرياض':    'Transport',
    'riyadh bus':       'Transport',
    'hafilat':          'Transport',
    'سابتكو':           'Transport',
    'saptco':           'Transport',
    'مواقف':            'Transport',
    'mawaqif':          'Transport',
    'باص':              'Transport',
    # Shopping
    'امازون':           'Shopping',
    'amazon':           'Shopping',
    'نون':              'Shopping',
    'noon':             'Shopping',
    'جرير':             'Shopping',
    'jarir':            'Shopping',
    'ايكيا':            'Shopping',
    'ikea':             'Shopping',
    'زارا':             'Shopping',
    'zara':             'Shopping',
    'H&M':              'Shopping',
    'h&m':              'Shopping',
    'extra':            'Shopping',
    'إكسترا':           'Shopping',
    'سوني':             'Shopping',
    'apple store':      'Shopping',
    'متجر ابل':         'Shopping',
    # Bills & Utilities
    'stc':              'Bills & Utilities',
    'موبايلي':          'Bills & Utilities',
    'mobily':           'Bills & Utilities',
    'زين':              'Bills & Utilities',
    'zain':             'Bills & Utilities',
    'فودافون':          'Bills & Utilities',
    'vodafone':         'Bills & Utilities',
    'الكهرباء':         'Bills & Utilities',
    'electricity':      'Bills & Utilities',
    'sesco':            'Bills & Utilities',
    'marafiq':          'Bills & Utilities',
    'مرافق':            'Bills & Utilities',
    'المياه':           'Bills & Utilities',
    'water':            'Bills & Utilities',
    'الغاز':            'Bills & Utilities',
    'bill payment':     'Bills & Utilities',
    'فاتورة':           'Bills & Utilities',
    'sadad':            'Bills & Utilities',
    'سداد':             'Bills & Utilities',
    # Health
    'صيدلية النهدي':    'Health',
    'alnahdi':          'Health',
    'al-nahdi':         'Health',
    'صيدلية الدواء':    'Health',
    'al dawa':          'Health',
    'al-dawa':          'Health',
    'صيدلية':           'Health',
    'pharmacy':         'Health',
    'مستشفى':           'Health',
    'hospital':         'Health',
    'clinic':           'Health',
    'عيادة':            'Health',
    # Entertainment
    'نتفليكس':          'Entertainment',
    'netflix':          'Entertainment',
    'سبوتيفاي':         'Entertainment',
    'spotify':          'Entertainment',
    'يوتيوب':           'Entertainment',
    'youtube':          'Entertainment',
    'apple music':      'Entertainment',
    'شاهد':             'Entertainment',
    'shahid':           'Entertainment',
    'سينما':            'Entertainment',
    'cinema':           'Entertainment',
    'vox':              'Entertainment',
    'amctheater':       'Entertainment',
    'playstation':      'Entertainment',
    'steam':            'Entertainment',
    # Transfers
    'تحويل':            'Transfers',
    'transfer':         'Transfers',
    'trf':              'Transfers',
    'راتب':             'Transfers',   # salary = income transfer
    'salary':           'Transfers',
    'إيداع':            'Transfers',
    'deposit':          'Transfers',
}


def lookup_category(merchant: str) -> str | None:
    """
    Check if the merchant matches a known Saudi merchant.
    Returns category string or None if not found.
    Case-insensitive substring match.
    """
    lower = merchant.lower()
    for key, cat in MERCHANT_DICT.items():
        if key.lower() in lower:
            return cat
    return None


# ── Claude prompt templates ───────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Saudi personal finance assistant. Your only job is to classify bank transactions into exactly one of these 8 categories:

1. Food & Dining      - restaurants, cafes, grocery stores, supermarkets
2. Transport          - taxis, ride-hailing, public transport, fuel, parking
3. Shopping           - retail stores, e-commerce, clothing, electronics
4. Bills & Utilities  - phone bills, electricity, water, internet, subscriptions to services
5. Health             - pharmacies, hospitals, clinics, medical supplies
6. Entertainment      - streaming services, cinemas, games, sports
7. Transfers          - money transfers, salary, deposits, withdrawals
8. Other              - anything that doesn't fit the above

Rules:
- Respond with ONLY a JSON array, no explanation, no markdown.
- Each element must have exactly two keys: "idx" (the transaction index from input) and "category" (one of the 8 exact strings above).
- If uncertain, choose the closest match. Never return null or unknown.
- Saudi merchant names may be in Arabic or English. Common ones: البيك=AlBaik(Food), هايبر باندا=Hyper Panda(Food), كريم=Careem(Transport), STC=Bills, النهدي=Pharmacy(Health).
"""

USER_PROMPT_TEMPLATE = """Classify these transactions:

{transactions_json}

Return only the JSON array."""
