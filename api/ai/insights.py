"""
Savings insights generator using Gemini Flash.
Analyses categorised transactions and returns 3-5 personalised insights.
"""

import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_NAME = 'gemini-1.5-flash'

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a personal finance advisor specialising in Saudi Arabia.
Analyse the user's bank transactions and return 3 to 5 actionable savings insights.

Rules:
- Respond with ONLY a valid JSON array, no markdown, no extra text.
- Each insight object must have these exact keys:
    title_ar    : short Arabic title (max 8 words)
    title_en    : short English title (max 8 words)
    body_ar     : 1-2 sentence Arabic explanation referencing actual amounts/merchants
    body_en     : 1-2 sentence English explanation referencing actual amounts/merchants
    tip_ar      : one actionable Arabic tip
    tip_en      : one actionable English tip
    type        : one of "warning", "success", "info"
- Use "warning" for overspending, "success" for good habits, "info" for neutral observations.
- Reference real numbers from the data (e.g. "أنفقت ٤٧٠ ريال على المطاعم").
- Keep tone friendly and encouraging, not judgmental.
- Insights should be diverse — don't repeat the same category.
"""

USER_PROMPT_TEMPLATE = """Here is a summary of the user's transactions:

Total Income:   {income:.2f} SAR
Total Expenses: {expenses:.2f} SAR
Net:            {net:.2f} SAR
Period:         {date_from} to {date_to}

Spending by category:
{category_breakdown}

Top merchants by spend:
{top_merchants}

Generate 3-5 personalised savings insights for this user."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_model():
    key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not key:
        logger.warning('GEMINI_API_KEY not set — returning fallback insights')
        return None
    genai.configure(api_key=key)
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
    )


def _build_summary(transactions: list[dict]) -> dict:
    income   = sum(t['amount'] for t in transactions if t['amount'] > 0)
    expenses = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)

    cat_totals: dict[str, float] = {}
    for t in transactions:
        if t['amount'] < 0:
            cat = t.get('category') or 'Other'
            cat_totals[cat] = cat_totals.get(cat, 0) + abs(t['amount'])

    merchant_totals: dict[str, float] = {}
    for t in transactions:
        if t['amount'] < 0:
            m = t.get('merchant', 'Unknown')
            merchant_totals[m] = merchant_totals.get(m, 0) + abs(t['amount'])

    top_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:8]
    dates = [t['date'] for t in transactions if t.get('date')]

    return {
        'income':        income,
        'expenses':      expenses,
        'net':           income - expenses,
        'date_from':     min(dates, default=''),
        'date_to':       max(dates, default=''),
        'cat_totals':    cat_totals,
        'top_merchants': top_merchants,
    }


def _build_prompt(summary: dict) -> str:
    cat_lines = '\n'.join(
        f'  {cat}: {total:.2f} SAR'
        for cat, total in sorted(summary['cat_totals'].items(), key=lambda x: x[1], reverse=True)
    )
    merch_lines = '\n'.join(
        f'  {name}: {total:.2f} SAR'
        for name, total in summary['top_merchants']
    )
    return USER_PROMPT_TEMPLATE.format(
        income=summary['income'],
        expenses=summary['expenses'],
        net=summary['net'],
        date_from=summary['date_from'],
        date_to=summary['date_to'],
        category_breakdown=cat_lines or '  (no expenses)',
        top_merchants=merch_lines or '  (none)',
    )


def _fallback_insights(summary: dict) -> list[dict]:
    """Rule-based insights when API is unavailable."""
    insights = []
    expenses = summary['expenses']
    income   = summary['income']

    if income > 0:
        savings_rate = (summary['net'] / income) * 100
        if savings_rate >= 20:
            insights.append({
                'title_ar': 'معدل ادخار ممتاز',
                'title_en': 'Great Savings Rate',
                'body_ar':  f'وفّرت {savings_rate:.0f}٪ من دخلك هذا الشهر. استمر على هذا المستوى!',
                'body_en':  f'You saved {savings_rate:.0f}% of your income this month. Keep it up!',
                'tip_ar':   'فكّر في استثمار جزء من هذه المدخرات.',
                'tip_en':   'Consider investing a portion of these savings.',
                'type':     'success',
            })
        elif savings_rate < 0:
            insights.append({
                'title_ar': 'مصروفاتك تتجاوز دخلك',
                'title_en': 'Spending Exceeds Income',
                'body_ar':  f'أنفقت {abs(savings_rate):.0f}٪ أكثر من دخلك هذا الشهر.',
                'body_en':  f'You spent {abs(savings_rate):.0f}% more than your income this month.',
                'tip_ar':   'راجع مصروفاتك وحدّد أين يمكن التوفير.',
                'tip_en':   'Review your expenses and identify where you can cut back.',
                'type':     'warning',
            })

    if summary['cat_totals']:
        top_cat, top_amt = max(summary['cat_totals'].items(), key=lambda x: x[1])
        if expenses > 0 and (top_amt / expenses) > 0.35:
            insights.append({
                'title_ar': f'إنفاق مرتفع على {top_cat}',
                'title_en': f'High Spend on {top_cat}',
                'body_ar':  f'أنفقت {top_amt:.0f} ريال على {top_cat}، وهو {top_amt/expenses*100:.0f}٪ من إجمالي مصروفاتك.',
                'body_en':  f'You spent {top_amt:.0f} SAR on {top_cat}, which is {top_amt/expenses*100:.0f}% of your total expenses.',
                'tip_ar':   'حاول تقليل هذا البند بنسبة ١٠–١٥٪ الشهر القادم.',
                'tip_en':   'Try to reduce this category by 10-15% next month.',
                'type':     'warning',
            })

    if not insights:
        insights.append({
            'title_ar': 'تتبع مصروفاتك',
            'title_en': 'Track Your Spending',
            'body_ar':  'تتبع مصروفاتك بانتظام يساعدك على اتخاذ قرارات مالية أفضل.',
            'body_en':  'Regularly tracking your expenses helps you make better financial decisions.',
            'tip_ar':   'خصص ١٠ دقائق أسبوعياً لمراجعة مصروفاتك.',
            'tip_en':   'Set aside 10 minutes weekly to review your expenses.',
            'type':     'info',
        })

    return insights


def _parse_response(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1].rsplit('```', 1)[0]
    try:
        data = json.loads(text)
        required = {'title_ar', 'title_en', 'body_ar', 'body_en', 'tip_ar', 'tip_en', 'type'}
        valid = [i for i in data if required.issubset(i.keys())]
        return valid[:5]
    except Exception as e:
        logger.error('Failed to parse insights response: %s', e)
        return []


# ── Public entry point ────────────────────────────────────────────────────────

def generate_insights(transactions: list[dict]) -> list[dict]:
    """Generate 3-5 savings insights from categorised transactions."""
    summary = _build_summary(transactions)
    model   = _get_model()

    if model is None:
        return _fallback_insights(summary)

    prompt = _build_prompt(summary)

    try:
        response = model.generate_content(prompt)
        insights = _parse_response(response.text)
        if insights:
            return insights
        logger.warning('Gemini returned empty insights — using fallback')
        return _fallback_insights(summary)
    except Exception as e:
        logger.error('Gemini API error for insights: %s', e)
        return _fallback_insights(summary)
