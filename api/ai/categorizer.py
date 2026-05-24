"""
Transaction categorizer.
Strategy:
  1. Dictionary lookup for known Saudi merchants  (free, instant)
  2. Gemini Flash for everything else             (batched, free tier)
  3. Graceful fallback to 'Other' if API fails
"""

import json
import logging
import google.generativeai as genai
from django.conf import settings

from .prompts import (
    CATEGORIES_AR, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, lookup_category
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 50
MODEL_NAME = 'gemini-1.5-flash'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_model():
    key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not key:
        logger.warning('GEMINI_API_KEY not set — skipping AI categorization')
        return None
    genai.configure(api_key=key)
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
    )


def _parse_response(text: str) -> dict[int, str]:
    """Extract {idx: category} map from Gemini's JSON response."""
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1].rsplit('```', 1)[0]
    try:
        data = json.loads(text)
        return {item['idx']: item['category'] for item in data}
    except Exception as e:
        logger.error('Failed to parse Gemini response: %s\nRaw: %s', e, text[:300])
        return {}


def _call_gemini(model, batch: list[dict]) -> dict[int, str]:
    """Send one batch to Gemini and return {local_idx: category} map."""
    payload = [
        {'idx': i, 'merchant': t['merchant'], 'original': t.get('original_text', '')}
        for i, t in enumerate(batch)
    ]
    prompt = USER_PROMPT_TEMPLATE.format(
        transactions_json=json.dumps(payload, ensure_ascii=False, indent=None)
    )
    try:
        response = model.generate_content(prompt)
        return _parse_response(response.text)
    except Exception as e:
        logger.error('Gemini API error: %s', e)
        return {}


# ── Public entry point ────────────────────────────────────────────────────────

def categorize(transactions: list[dict]) -> list[dict]:
    """
    Categorize a list of transaction dicts in-place.
    Returns the same list with 'category' and 'category_ar' filled in.
    """
    # ── Step 1: dictionary pre-pass ──────────────────────────────────────────
    needs_ai: list[int] = []

    for i, t in enumerate(transactions):
        if t.get('category'):
            continue
        cat = lookup_category(t.get('merchant', '') + ' ' + t.get('original_text', ''))
        if cat:
            t['category']    = cat
            t['category_ar'] = CATEGORIES_AR.get(cat, '')
        else:
            needs_ai.append(i)

    if not needs_ai:
        return transactions   # 100% dictionary hit — no API needed

    # ── Step 2: Gemini for unknowns ──────────────────────────────────────────
    model = _get_model()

    if model is None:
        for i in needs_ai:
            transactions[i]['category']    = 'Other'
            transactions[i]['category_ar'] = CATEGORIES_AR['Other']
        return transactions

    for batch_start in range(0, len(needs_ai), BATCH_SIZE):
        batch_indices = needs_ai[batch_start: batch_start + BATCH_SIZE]
        batch_txns    = [transactions[i] for i in batch_indices]

        result_map = _call_gemini(model, batch_txns)

        for local_idx, global_idx in enumerate(batch_indices):
            cat = result_map.get(local_idx, 'Other')
            if cat not in CATEGORIES_AR:
                cat = 'Other'
            transactions[global_idx]['category']    = cat
            transactions[global_idx]['category_ar'] = CATEGORIES_AR.get(cat, '')

    return transactions
