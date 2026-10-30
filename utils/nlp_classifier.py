"""
NLP Classifier Module
=====================
Loads the trained scikit-learn model pipeline from model.joblib and performs
offline category inference with probability confidence scores and low-confidence fallback.
"""

import os
import re
import joblib
from utils.db import get_db

_MODEL_PIPELINE = None


def clean_text(text):
    """Normalize input text for model inference."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[\d₹]+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_model(model_path=None):
    """
    Lazy singleton loader for model.joblib.
    If model file is missing, trains the model on the fly.
    """
    global _MODEL_PIPELINE
    if _MODEL_PIPELINE is not None:
        return _MODEL_PIPELINE

    if model_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, 'model.joblib')

    if not os.path.exists(model_path):
        from train_model import train
        _MODEL_PIPELINE, _ = train(model_output_path=model_path)
    else:
        _MODEL_PIPELINE = joblib.load(model_path)

    return _MODEL_PIPELINE


def predict_category(text, confidence_threshold=0.5):
    """
    Predict expense category and confidence score for a given text.
    Returns:
        {
            'category': 'Food',              # effective category (defaults to 'Other' if low confidence)
            'predicted_category': 'Food',    # raw model prediction
            'confidence': 0.94,              # probability (0.0 to 1.0)
            'is_low_confidence': False       # True if confidence < threshold
        }
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            'category': 'Other',
            'predicted_category': 'Other',
            'confidence': 0.0,
            'is_low_confidence': True
        }

    pipeline = load_model()
    classes = pipeline.classes_
    probabilities = pipeline.predict_proba([cleaned])[0]

    max_idx = int(probabilities.argmax())
    max_prob = float(probabilities[max_idx])
    predicted_label = str(classes[max_idx])

    confidence = round(max_prob, 2)
    is_low_conf = confidence < confidence_threshold

    effective_category = 'Other' if is_low_conf else predicted_label

    return {
        'category': effective_category,
        'predicted_category': predicted_label,
        'confidence': confidence,
        'is_low_confidence': is_low_conf
    }


def get_category_id_by_name(category_name):
    """Look up database ID for a given category name."""
    STATIC_MAP = {
        'food': 1, 'travel': 2, 'shopping': 3, 'bills': 4,
        'entertainment': 5, 'health': 6, 'education': 7, 'other': 8
    }
    try:
        db = get_db()
        cursor = db.execute("SELECT id FROM categories WHERE name = ? COLLATE NOCASE", (category_name,))
        row = cursor.fetchone()
        if row:
            return row['id']
        # Fallback to Other
        cursor = db.execute("SELECT id FROM categories WHERE name = 'Other'")
        fallback_row = cursor.fetchone()
        return fallback_row['id'] if fallback_row else 8
    except RuntimeError:
        # Outside Flask application context (CLI, scripts, standalone tests)
        return STATIC_MAP.get(str(category_name).lower(), 8)
