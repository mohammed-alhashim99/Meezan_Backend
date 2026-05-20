import anthropic
from django.conf import settings
from .prompts import CATEGORIES, CATEGORIES_AR


def categorize(transactions: list[dict]) -> list[dict]:
    """Send transactions to Claude and return them with category fields added."""
    # Day 6 implementation
    raise NotImplementedError
