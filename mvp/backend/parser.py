"""
Zero-hallucination query parser for the Ask Photos Co-Pilot.

Turns a messy natural-language memory ("that rainy beach trip with friends")
into a strict, structured JSON of allowed facet keys. Never generates text,
never invents values that aren't in the catalog's own vocabulary — it only
ever assigns a value if it is also an actual value in the database. This
makes hallucination structurally impossible: worst case, a facet stays null.

Primary path: keyword/synonym matching (free, instant, no external calls).
Optional path: a local Ollama model can be used to do the same extraction
task if OLLAMA_URL is reachable, purely as a "fancier NLU" upgrade — the
output is still forced through the same catalog-vocabulary validation before
it's trusted, so it can't hallucinate a value the database doesn't contain.
"""

import os
import re
import requests

from database import MOCK_PHOTOS, CATEGORICAL_KEYS, get_facet_values

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
USE_OLLAMA = os.environ.get("USE_OLLAMA", "false").lower() == "true"

# Synonym map: extra words that should resolve to a real catalog value.
# Keys are catalog values (as they appear in database.py); values are
# additional trigger words a user might type instead.
SYNONYMS = {
    "Rainy": ["rain", "raining", "rained", "monsoon", "wet"],
    "Sunny": ["sun", "sunshine", "bright", "hot day"],
    "Cloudy": ["overcast", "grey sky", "gray sky"],
    "Clear": ["clear sky", "clear skies"],
    "Outdoor": ["outside", "outdoors"],
    "Indoor": ["inside", "indoors"],
    "Mountain": ["mountains", "hills", "hill station"],
    "Friends": ["friend", "buddies", "mates", "crew"],
    "Family": ["mom", "dad", "parents", "kids", "relatives"],
    "Alone": ["solo", "by myself", "just me"],
    "Dog": ["puppy", "pet"],
    "Screenshot": ["screenshots", "wifi password", "wi-fi password"],
}


def _build_vocab():
    """Map every lowercase trigger word -> (facet_key, canonical_value)."""
    vocab = {}
    for key in CATEGORICAL_KEYS:
        for value in get_facet_values(key):
            vocab[value.lower()] = (key, value)
            for synonym in SYNONYMS.get(value, []):
                vocab[synonym.lower()] = (key, value)
    return vocab


VOCAB = _build_vocab()


def _keyword_parse(user_query):
    text = user_query.lower()
    result = {key: None for key in CATEGORICAL_KEYS}
    for trigger, (facet_key, canonical_value) in VOCAB.items():
        if re.search(r"\b" + re.escape(trigger) + r"\b", text):
            result[facet_key] = canonical_value
    return result


def _validate_against_catalog(parsed):
    """Guardrail: drop any value the LLM invented that isn't a real catalog value."""
    clean = {key: None for key in CATEGORICAL_KEYS}
    for key in CATEGORICAL_KEYS:
        value = parsed.get(key)
        if value and value in get_facet_values(key):
            clean[key] = value
    return clean


def _ollama_parse(user_query):
    allowed = ", ".join(CATEGORICAL_KEYS)
    prompt = f"""You are a strict data extraction tool. Extract matching attributes from the user's photo search query.
Respond ONLY with a valid JSON object. Do not include any explanations, markdown formatting, or extra text.

Allowed keys: {allowed}
If a key is not mentioned, set its value to null.

User Query: "{user_query}"
"""
    payload = {"model": "llama3.2", "prompt": prompt, "stream": False, "format": "json"}
    response = requests.post(OLLAMA_URL, json=payload, timeout=5)
    response.raise_for_status()
    import json
    return json.loads(response.json()["response"])


def parse_vague_query(user_query):
    """
    Returns a dict of {location, setting, weather, people, object} -> value|None.
    Every non-null value is guaranteed to exist in the mock catalog's vocabulary.
    """
    if USE_OLLAMA:
        try:
            parsed = _ollama_parse(user_query)
            return _validate_against_catalog(parsed)
        except Exception:
            pass  # fall through to deterministic keyword parsing

    return _keyword_parse(user_query)
