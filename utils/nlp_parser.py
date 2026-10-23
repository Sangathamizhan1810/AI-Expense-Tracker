"""
NLP Parser Module: Regex Amount Extraction & Sentence Parsing
=============================================================
Parses natural language expense sentences (e.g., "Swiggy 250", "paid 35 for tea",
"₹1200 electricity bill"), extracts numeric amounts, cleanses descriptions, and
invokes the ML model for category prediction.
"""

import re
from datetime import date
from utils.nlp_classifier import predict_category, get_category_id_by_name


def extract_amount(text):
    """
    Extract numeric amount from sentence and return (amount_or_none, cleaned_description).
    Handles formats:
      - 'Swiggy 250' -> (250.0, 'Swiggy')
      - '₹500 petrol' -> (500.0, 'petrol')
      - 'rs. 45.50 coffee' -> (45.50, 'coffee')
      - 'auto 40 rs' -> (40.0, 'auto')
      - 'paid 1200 for electricity bill' -> (1200.0, 'paid for electricity bill')
      - 'lunch buffet' -> (None, 'lunch buffet')
    """
    if not text:
        return None, ""

    raw = text.strip()

    # Pattern 1: Currency prefix e.g. "₹ 250", "rs 45.50", "rs. 100", "inr 500"
    prefix_match = re.search(r'(?:₹|rs\.?|inr)\s*(\d+(?:\.\d{1,2})?)\b', raw, re.IGNORECASE)
    if prefix_match:
        amount_val = float(prefix_match.group(1))
        # Remove matched currency prefix + amount
        start, end = prefix_match.span()
        residual = (raw[:start] + ' ' + raw[end:]).strip()
        cleaned_desc = _clean_residual_text(residual)
        return amount_val, cleaned_desc

    # Pattern 2: Currency suffix e.g. "250 rs", "45.50 rupees", "1000 inr", "50 ₹"
    suffix_match = re.search(r'\b(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|rupees?|inr)\b', raw, re.IGNORECASE)
    if suffix_match:
        amount_val = float(suffix_match.group(1))
        start, end = suffix_match.span()
        residual = (raw[:start] + ' ' + raw[end:]).strip()
        cleaned_desc = _clean_residual_text(residual)
        return amount_val, cleaned_desc

    # Pattern 3: Number at the very end of sentence e.g. "Swiggy 250", "bus ticket 30"
    end_match = re.search(r'\b(\d+(?:\.\d{1,2})?)\s*$', raw)
    if end_match:
        amount_val = float(end_match.group(1))
        start, end = end_match.span()
        residual = raw[:start].strip()
        cleaned_desc = _clean_residual_text(residual)
        return amount_val, cleaned_desc

    # Pattern 4: Any standalone number in the sentence e.g. "paid 50 for chai"
    standalone_match = re.search(r'\b(\d+(?:\.\d{1,2})?)\b', raw)
    if standalone_match:
        amount_val = float(standalone_match.group(1))
        start, end = standalone_match.span()
        residual = (raw[:start] + ' ' + raw[end:]).strip()
        cleaned_desc = _clean_residual_text(residual)
        return amount_val, cleaned_desc

    # No numeric amount found
    return None, _clean_residual_text(raw)


def _clean_residual_text(text):
    """Clean up leftover text: remove standalone currency words, symbols, and extra spaces."""
    if not text:
        return ""
    # Strip currency tokens that might be left
    text = re.sub(r'\b(?:₹|rs\.?|rupees?|inr)\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'[₹]+', ' ', text)
    # Collapse multiple whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_expense_sentence(sentence, confidence_threshold=0.5):
    """
    Parse natural language sentence:
    1. Extract numeric amount
    2. Extract description
    3. Predict category via ML classifier
    4. Resolve database category_id
    Returns structured dict ready for UI consumption or DB persistence.
    """
    sentence = (sentence or '').strip()
    amount, description = extract_amount(sentence)

    # Use description or full sentence for classification
    text_to_classify = description if description else sentence
    prediction = predict_category(text_to_classify, confidence_threshold=confidence_threshold)

    category_name = prediction['category']
    category_id = get_category_id_by_name(category_name)

    # Clean description for display / storage: capitalize nicely if available
    display_description = description if description else sentence

    return {
        'raw_input': sentence,
        'amount': amount,
        'description': display_description,
        'category_name': category_name,
        'predicted_category': prediction['predicted_category'],
        'category_id': category_id,
        'confidence': prediction['confidence'],
        'is_low_confidence': prediction['is_low_confidence'],
        'expense_date': date.today().isoformat()
    }
