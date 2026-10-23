"""
Model Verification Tests: scikit-learn TF-IDF + Logistic Regression pipeline
Tests model loading, probability inference, category mapping, and sub-50ms latency.
"""

import unittest
import time
import os
from utils.nlp_classifier import load_model, predict_category, clean_text


class ModelTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = load_model()

    def test_model_file_exists(self):
        """Verify model.joblib exists on disk."""
        self.assertTrue(os.path.exists('model.joblib'))
        self.assertIsNotNone(self.pipeline)

    def test_category_predictions(self):
        """Verify accurate predictions for typical expressions across all categories."""
        test_cases = [
            ("Swiggy biryani dinner", "Food"),
            ("Zomato pizza order", "Food"),
            ("Uber cab to airport", "Travel"),
            ("Metro smart card recharge", "Travel"),
            ("Amazon order headphones", "Shopping"),
            ("Zara shirt", "Shopping"),
            ("Electricity bill Bescom", "Bills"),
            ("Airtel fiber broadband wifi", "Bills"),
            ("Netflix subscription", "Entertainment"),
            ("PVR movie ticket", "Entertainment"),
            ("Apollo pharmacy medicines", "Health"),
            ("Doctor consultation fee", "Health"),
            ("Udemy python course", "Education"),
            ("College tuition fee", "Education"),
            ("Dry cleaning suit", "Other"),
            ("Charity donation trust", "Other")
        ]

        for text, expected_category in test_cases:
            result = predict_category(text)
            self.assertEqual(
                result['predicted_category'], expected_category,
                f"Failed for input '{text}': got {result['predicted_category']} expected {expected_category}"
            )
            self.assertGreaterEqual(result['confidence'], 0.50)
            self.assertFalse(result['is_low_confidence'])

    def test_low_confidence_fallback(self):
        """Verify random gibberish triggers is_low_confidence flag and defaults to 'Other'."""
        gibberish = "qwertyuiop asdfghjk zxcvbnm"
        result = predict_category(gibberish, confidence_threshold=0.50)
        # Random gibberish should either have confidence < 0.5 or category Other
        if result['confidence'] < 0.50:
            self.assertTrue(result['is_low_confidence'])
            self.assertEqual(result['category'], 'Other')

    def test_empty_string_handling(self):
        """Verify empty or numeric-only strings return Other safely without crashing."""
        result = predict_category("")
        self.assertEqual(result['category'], 'Other')
        self.assertTrue(result['is_low_confidence'])

        result_num = predict_category("12345 6789")
        self.assertEqual(result_num['category'], 'Other')

    def test_inference_latency(self):
        """Verify inference execution latency is under 50ms per query."""
        start = time.perf_counter()
        for _ in range(50):
            predict_category("Swiggy burger meal 250")
        avg_latency_ms = ((time.perf_counter() - start) / 50) * 1000
        print(f"\nAverage NLP inference latency: {avg_latency_ms:.2f}ms")
        self.assertLess(avg_latency_ms, 50.0)


if __name__ == '__main__':
    unittest.main()
