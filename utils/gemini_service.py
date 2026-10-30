"""
Gemini AI Service Module
========================
Provides cloud-powered natural language expense categorization and entity extraction
using Google Gemini API (gemini-3.1-flash-lite / gemini-3.8-flash) as an intelligent
knowledge layer over the local ML model.
"""

import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = {
    'Food', 'Travel', 'Shopping', 'Bills',
    'Entertainment', 'Health', 'Education', 'Other'
}

GEMINI_MODELS = [
    'gemini-3.1-flash-lite',
    'gemini-3.8-flash',
    'gemini-flash-latest'
]


def classify_with_gemini(sentence, timeout=5):
    """
    Query Google Gemini API with unlimited real-world knowledge to categorize
    an expense sentence (e.g., 'Biriyani 250', 'rapido bike 40', 'apollo pharmacy 120').

    Returns:
        dict: {
            'amount': float or None,
            'category': str,
            'description': str,
            'confidence': 0.95
        } or None if unavailable.
    """
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not api_key:
        return None, False

    sentence = (sentence or '').strip()
    if not sentence:
        return None, False

    prompt = f"""You are a financial classification assistant for an Expense Tracker app.
Categorize this user expense entry into exactly one of these categories:
[Food, Travel, Shopping, Bills, Entertainment, Health, Education, Other]

Allowed categories ONLY: Food, Travel, Shopping, Bills, Entertainment, Health, Education, Other.

Input entry: "{sentence}"

Task:
1. Extract numeric amount if mentioned (e.g. 250, 45.50). If no amount, return null.
2. Select the single most accurate category based on world knowledge (e.g., 'Biriyani' -> Food, 'Rapido' -> Travel, 'Dolo 650' -> Health, 'Netflix' -> Entertainment, 'Bescom' -> Bills).
3. Return a clean short title description.

Return ONLY a valid JSON object without markdown or code fences:
{{"amount": 250.0, "category": "Food", "description": "Biriyani"}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }
    encoded_data = json.dumps(payload).encode('utf-8')

    quota_exceeded = False

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                text_content = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
                if not text_content:
                    continue

                parsed = json.loads(text_content)
                cat = parsed.get('category', '').strip().capitalize()
                
                # Normalize category names to match DB exactly
                if cat not in ALLOWED_CATEGORIES:
                    matched = next((c for c in ALLOWED_CATEGORIES if c.lower() == cat.lower()), None)
                    cat = matched or 'Other'

                raw_amt = parsed.get('amount')
                amount = None
                if raw_amt is not None:
                    try:
                        amount = float(raw_amt)
                    except (ValueError, TypeError):
                        amount = None

                desc = (parsed.get('description') or sentence).strip()

                return {
                    'amount': amount,
                    'category': cat,
                    'description': desc,
                    'confidence': 0.95,
                    'source': 'gemini_ai'
                }, False
        except urllib.error.HTTPError as e:
            if e.code == 429:
                quota_exceeded = True
                logger.warning("Gemini quota exceeded (HTTP 429): %s", e)
                break
            elif e.code in (400, 401, 403):
                logger.warning("Gemini auth/key error (HTTP %s): %s", e.code, e)
                break
            else:
                logger.debug("Gemini model %s HTTP error: %s", model, e)
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
            logger.debug("Gemini model %s query failed: %s", model, e)
            continue
        except Exception as e:
            logger.warning("Unexpected error during Gemini classification: %s", e)
            break

    return None, quota_exceeded
