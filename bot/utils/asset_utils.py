import string
from typing import List, Dict


def get_next_alias(existing_aliases: List[str]) -> str:
    """Get next available alias (A, B, C, ...)"""
    used_aliases = set(existing_aliases)
    for letter in string.ascii_uppercase:
        if letter not in used_aliases:
            return letter
    # If all single letters are used, use AA, AB, etc.
    for first in string.ascii_uppercase:
        for second in string.ascii_uppercase:
            alias = first + second
            if alias not in used_aliases:
                return alias
    raise Exception("Too many assets (max 702)")
