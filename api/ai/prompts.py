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
# Pre-classify ~160 well-known Saudi merchants to save API calls & improve accuracy.
# Keys are lowercase substrings; first match wins.
# Sources: OpenStreetMap Saudi Arabia, data.gov.sa, SFDA, Argaam, xMap

MERCHANT_DICT: dict[str, str] = {

    # ── Food & Dining: Saudi fast-food chains ────────────────────────────────
    'هايبر باندا':      'Food & Dining',
    'hyper panda':      'Food & Dining',
    'البيك':            'Food & Dining',
    'albaik':           'Food & Dining',
    'al-baik':          'Food & Dining',
    'al baik':          'Food & Dining',
    'هرفي':             'Food & Dining',   # Herfy — Saudi burgers/chicken chain
    'herfy':            'Food & Dining',
    'كودو':             'Food & Dining',   # Kudu — sandwiches/chicken
    'kudu':             'Food & Dining',
    'شاورمر':           'Food & Dining',   # Shawarmer
    'shawarmer':        'Food & Dining',
    'التاج':            'Food & Dining',   # Al Tazaj — grilled chicken
    'al tazaj':         'Food & Dining',
    'tazaj':            'Food & Dining',
    'الرومانسية':       'Food & Dining',   # Al Romansiah — mandi/kabsa
    'romansiah':        'Food & Dining',
    'ماما نورة':        'Food & Dining',
    'mama noura':       'Food & Dining',
    # International fast food
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
    'باسكن روبنز':      'Food & Dining',
    'baskin':           'Food & Dining',
    'سبواي':            'Food & Dining',
    'subway':           'Food & Dining',
    'بيتزا هت':         'Food & Dining',
    'pizza hut':        'Food & Dining',
    'دومينوز':          'Food & Dining',
    'domino':           'Food & Dining',
    'بيت الكبسة':       'Food & Dining',
    'bait alkabsa':     'Food & Dining',
    # Grocery / supermarkets
    'تميمي':            'Food & Dining',
    'tamimi':           'Food & Dining',
    'بنده':             'Food & Dining',
    'panda':            'Food & Dining',
    'bindawood':        'Food & Dining',
    'بن داود':          'Food & Dining',
    'لولو':             'Food & Dining',
    'lulu':             'Food & Dining',
    'ليان':             'Food & Dining',
    'leean':            'Food & Dining',
    'العثيم':           'Food & Dining',   # Al-Othaim Markets — 227 stores
    'othaim':           'Food & Dining',
    'الدانوب':          'Food & Dining',   # Danube — BinDawood Holding
    'danube':           'Food & Dining',
    'فارم':             'Food & Dining',   # Farm Superstores — Eastern region
    'farm superstore':  'Food & Dining',
    'الراية':           'Food & Dining',   # Al Raya — now Tamimi
    'al raya':          'Food & Dining',
    'كارفور':           'Food & Dining',   # Carrefour
    'carrefour':        'Food & Dining',
    'nesto':            'Food & Dining',   # Nesto — UAE-origin growing in KSA
    'نيستو':            'Food & Dining',
    # Delivery apps (merchant = aggregator)
    'هنقرستيشن':        'Food & Dining',   # HungerStation
    'hungerstation':    'Food & Dining',
    'جاهز':             'Food & Dining',   # Jahez
    'jahez':            'Food & Dining',
    'طلبات':            'Food & Dining',   # Talabat
    'talabat':          'Food & Dining',
    'noon food':        'Food & Dining',
    'مرسول':            'Food & Dining',   # Marsool delivery
    'marsool':          'Food & Dining',
    # Generic food keywords
    'مطاعم':            'Food & Dining',
    'مطعم':             'Food & Dining',
    'كافيه':            'Food & Dining',
    'cafe':             'Food & Dining',
    'مقهى':             'Food & Dining',
    'حلويات':           'Food & Dining',
    'bakery':           'Food & Dining',
    'مخبز':             'Food & Dining',
    'restaurant':       'Food & Dining',

    # ── Transport ────────────────────────────────────────────────────────────
    'كريم':             'Transport',
    'careem':           'Transport',
    'اوبر':             'Transport',
    'uber':             'Transport',
    'جيني':             'Transport',
    'jeeny':            'Transport',
    'تكسي':             'Transport',
    'حافلات الرياض':    'Transport',
    'riyadh bus':       'Transport',
    'hafilat':          'Transport',
    'سابتكو':           'Transport',
    'saptco':           'Transport',
    'مواقف':            'Transport',
    'mawaqif':          'Transport',
    'باص':              'Transport',
    # Gas stations — Saudi chains (source: Argaam / xMap)
    'الدريس':           'Transport',   # Aldrees — largest chain, 1,231 stations
    'aldrees':          'Transport',
    'ساسكو':            'Transport',   # SASCO — ~630 stations
    'sasco':            'Transport',
    'بتروميم':          'Transport',   # Petromin
    'petromin':         'Transport',
    'j-oil':            'Transport',   # J-Oil — 175 stations
    'jiyol':            'Transport',
    'مزايا للوقود':     'Transport',   # Mazaya Fuel
    'mazaya fuel':      'Transport',
    'وقود':             'Transport',
    'fuel':             'Transport',
    'aramco':           'Transport',
    'بترومين':          'Transport',
    'سيارة':            'Transport',
    'parking':          'Transport',
    'بارك':             'Transport',

    # ── Shopping ─────────────────────────────────────────────────────────────
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
    'apple store':      'Shopping',
    'متجر ابل':         'Shopping',
    'shein':            'Shopping',
    'شي إن':            'Shopping',
    'lifestyle':        'Shopping',   # Lifestyle stores (seen in bank statements)
    'سوق':              'Shopping',
    'مول':              'Shopping',
    'mall':             'Shopping',
    # Digital payments (categorize as last used — keep as Shopping generic)
    'apple pay':        'Shopping',
    'google pay':       'Shopping',
    'stc pay':          'Shopping',
    'mada':             'Shopping',

    # ── Bills & Utilities ────────────────────────────────────────────────────
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
    'jawwy':            'Bills & Utilities',
    'جوي':              'Bills & Utilities',
    'النت':             'Bills & Utilities',
    'internet':         'Bills & Utilities',
    'broadband':        'Bills & Utilities',
    'ايتصالات':         'Bills & Utilities',
    'etisalat':         'Bills & Utilities',

    # ── Health ───────────────────────────────────────────────────────────────
    'صيدلية النهدي':    'Health',
    'النهدي':           'Health',
    'alnahdi':          'Health',
    'al-nahdi':         'Health',
    'nahdi':            'Health',
    'صيدلية الدواء':    'Health',
    'الدواء':           'Health',
    'aldawaa':          'Health',
    'al dawa':          'Health',
    'al-dawa':          'Health',
    'يونايتد فارماسي':  'Health',   # United Pharmacy
    'united pharmacy':  'Health',
    'كنوز':             'Health',   # Kunooz Pharmacy
    'kunooz':           'Health',
    'وايتس':            'Health',   # Whites Pharmacy
    'whites pharmacy':  'Health',
    'آستر':             'Health',   # Aster Pharmacy
    'aster':            'Health',
    'تداوي':            'Health',   # Tadawi
    'tadawi':           'Health',
    'بلانيت فارماسي':   'Health',   # Planet Pharmacy
    'planet pharmacy':  'Health',
    'صيدلية':           'Health',
    'pharmacy':         'Health',
    'مستشفى':           'Health',
    'hospital':         'Health',
    'clinic':           'Health',
    'عيادة':            'Health',
    'medical':          'Health',
    'طبي':              'Health',
    'دواء':             'Health',

    # ── Entertainment ────────────────────────────────────────────────────────
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
    'vox':              'Entertainment',   # VOX Cinemas
    'amctheater':       'Entertainment',
    'amc':              'Entertainment',
    'موفي':             'Entertainment',   # Muvi Cinemas — largest Saudi cinema chain
    'muvi':             'Entertainment',
    'سينيبوليس':        'Entertainment',   # Cinépolis
    'cinepolis':        'Entertainment',
    'ريل سينما':        'Entertainment',   # Reel Cinemas
    'reel cinema':      'Entertainment',
    'playstation':      'Entertainment',
    'steam':            'Entertainment',
    'xbox':             'Entertainment',
    'gaming':           'Entertainment',
    'inemas':           'Entertainment',   # catches "inemas" typo in bank statements

    # ── Transfers ────────────────────────────────────────────────────────────
    'تحويل':            'Transfers',
    'transfer':         'Transfers',
    'trf':              'Transfers',
    'راتب':             'Transfers',
    'salary':           'Transfers',
    'إيداع':            'Transfers',
    'deposit':          'Transfers',
    'حوالة':            'Transfers',
    'ref arnb':         'Transfers',   # ANB bank reference
    'ref ncbk':         'Transfers',   # NCB/SNB bank reference
    'ref snb':          'Transfers',
    'ref inma':         'Transfers',
    'ref rajh':         'Transfers',
    'imps':             'Transfers',
    'neft':             'Transfers',
    'upi':              'Transfers',   # Indian UPI (fake/test PDF)
    'paytm':            'Transfers',
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
