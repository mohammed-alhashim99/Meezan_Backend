"""
Transaction categorizer.
Strategy:
  1. Dictionary lookup for known Saudi merchants  (free, instant)
  2. Claude Haiku for everything else             (batched, cheap)
  3. Graceful fallback to 'Other' if API fails
"""

import json
import logging
import anthropic
from django.conf import settings

from .prompts import (
    CATEGORIES_AR, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, lookup_category
)

logger = logging.getLogger(__name__)

BATCH_SIZE   = 50    # transactions per Claude call
MODEL_HAIKU  = 'claude-haiku-4-5'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_client() -> anthropic.Anthropic | None:
    key = getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
    if not key:
        logger.warning('ANTHROPIC_API_KEY not set — skipping AI categorization')
        return None
    return anthropic.Anthropic(api_key=key)


def _parse_claude_response(text: str) -> dict[int, str]:
    """Extract {idx: category} map from Claude's JSON response."""
    # Strip any accidental markdown fences
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1].rsplit('```', 1)[0]

    try:
        data = json.loads(text)
        return {item['idx']: item['category'] for item in data}
    except Exception as e:
        logger.error('Failed to parse Claude response: %s\nRaw: %s', e, text[:300])
        return {}


def _call_claude(client: anthropic.Anthropic, batch: list[dict]) -> dict[int, str]:
    """Send one batch to Claude and return {local_idx: category} map."""
    # Build a minimal representation to save tokens
    payload = [
        {'idx': i, 'merchant': t['merchant'], 'original': t.get('original_text', '')}
        for i, t in enumerate(batch)
    ]
    prompt = USER_PROMPT_TEMPLATE.format(
        transactions_json=json.dumps(payload, ensure_ascii=False, indent=None)
    )

    try:
        msg = client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return _parse_claude_response(msg.content[0].text)
    except anthropic.RateLimitError:
        logger.warning('Claude rate limit hit — returning Other for this batch')
        return {}
    except anthropic.APIError as e:
        logger.error('Claude API error: %s', e)
        return {}


# ── Public entry point ────────────────────────────────────────────────────────

def categorize(transactions: list[dict]) -> list[dict]:
    """
    Categorize a list of transaction dicts in-place.
    Returns the same list with 'category' and 'category_ar' filled in.
    """
    # ── Step 1: dictionary pre-pass ──────────────────────────────────────────
    needs_claude: list[int] = []   # global indices still needing classification

    for i, t in enumerate(transactions):
        if t.get('category'):          # already categorised (e.g. user corrected)
            continue
        cat = lookup_category(t.get('merchant', '') + ' ' + t.get('original_text', ''))
        if cat:
            t['category']    = cat
            t['category_ar'] = CATEGORIES_AR.get(cat, '')
        else:
            needs_claude.append(i)

    if not needs_claude:
        return transactions   # 100% dictionary hit — no API needed

    # ── Step 2: Claude for unknowns ──────────────────────────────────────────
    client = _get_client()

    if client is None:
        # No API key — mark unknowns as Other
        for i in needs_claude:
            transactions[i]['category']    = 'Other'
            transactions[i]['category_ar'] = CATEGORIES_AR['Other']
        return transactions

    # Process in batches
    for batch_start in range(0, len(needs_claude), BATCH_SIZE):
        batch_indices = needs_claude[batch_start: batch_start + BATCH_SIZE]
        batch_txns    = [transactions[i] for i in batch_indices]

        result_map = _call_claude(client, batch_txns)

        for local_idx, global_idx in enumerate(batch_indices):
            cat = result_map.get(local_idx, 'Other')
            # Validate category is one of the 8
            if cat not in CATEGORIES_AR:
                cat = 'Other'
            transactions[global_idx]['category']    = cat
            transactions[global_idx]['category_ar'] = CATEGORIES_AR.get(cat, '')

    return transactions
