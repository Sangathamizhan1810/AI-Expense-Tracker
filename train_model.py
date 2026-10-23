"""
AI-Based Expense Tracker — Machine Learning Training Pipeline
=============================================================
Trains a scikit-learn TF-IDF + Logistic Regression pipeline on labelled
expense phrases across 8 categories, verifies >= 85% accuracy, and
serializes the trained model to model.joblib.
"""

import os
import re
import csv
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score


def clean_text(text):
    """Normalize text: lowercase, remove special characters and numbers."""
    if not text:
        return ""
    text = text.lower()
    # Remove numbers and standalone currency symbols
    text = re.sub(r'[\d₹]+', ' ', text)
    # Remove extra punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_dataset(csv_path):
    """Load expense texts and categories from CSV."""
    texts = []
    labels = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = clean_text(row['text'])
            cat = row['category'].strip()
            if cleaned and cat:
                texts.append(cleaned)
                labels.append(cat)
    return texts, labels


def train(data_path=None, model_output_path=None):
    """Train the model pipeline, evaluate, and save to disk."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if data_path is None:
        data_path = os.path.join(base_dir, 'data', 'expenses_dataset.csv')
    if model_output_path is None:
        model_output_path = os.path.join(base_dir, 'model.joblib')

    print(f"[*] Loading training data from: {data_path}")
    texts, labels = load_dataset(data_path)
    print(f"[*] Total dataset samples: {len(texts)}")

    # Ensure all 8 categories exist
    unique_labels = sorted(set(labels))
    print(f"[*] Target categories ({len(unique_labels)}): {unique_labels}")

    # Train-test split (80/20) with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )
    print(f"[*] Training samples: {len(X_train)} | Test samples: {len(X_test)}")

    # Build Pipeline: TF-IDF n-grams + Multinomial Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            strip_accents='unicode'
        )),
        ('clf', LogisticRegression(
            C=3.0,
            max_iter=1000,
            random_state=42,
            solver='lbfgs'
        ))
    ])

    print("[*] Training TF-IDF + Logistic Regression pipeline...")
    pipeline.fit(X_train, y_train)

    # Evaluate on held-out test split
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n[+] Test Set Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=unique_labels))

    # Requirement NLP-04: Test accuracy >= 85%
    if acc < 0.85:
        raise AssertionError(f"Model accuracy ({acc * 100:.2f}%) did not meet 85% requirement!")

    # Retrain on full dataset for maximum real-world inference accuracy
    print("[*] Retraining pipeline on full dataset for production inference...")
    pipeline.fit(texts, labels)

    # Serialize model to disk
    joblib.dump(pipeline, model_output_path)
    print(f"[+] Model serialized successfully to: {model_output_path}")
    return pipeline, acc


if __name__ == '__main__':
    train()
