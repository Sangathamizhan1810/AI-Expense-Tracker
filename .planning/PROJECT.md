# AI-Based Expense Tracker (Information System)

## What This Is

An AI-based personal expense tracking information system that helps students and young professionals record daily spending effortlessly, visualize financial habits, enforce monthly category budgets, and receive automated spending insights. Users can log transactions either through structured forms or by typing casual sentences (e.g., "Swiggy 250" or "bus ticket 30") which are parsed and categorized automatically using an offline machine learning model.

## Core Value

Frictionless expense logging through natural language sentence parsing and automatic categorization, coupled with exact budget enforcement and rule-based financial guidance—without requiring paid APIs or an active internet connection.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **AUTH-01**: User registration, secure login, password hashing, and session isolation.
- [ ] **EXP-01**: Expense recording with amount, category, date, and optional notes.
- [ ] **EXP-02**: Edit, update, and delete expense records.
- [ ] **EXP-03**: Filter expenses by date range and category with CSV export.
- [ ] **AI-01**: Natural language expense entry (e.g. "Swiggy 250") with regex amount extraction.
- [ ] **AI-02**: Offline scikit-learn TF-IDF + Logistic Regression category classifier with fallback to "Other" on confidence < 0.5.
- [ ] **BUD-01**: Category-specific monthly budget allocation.
- [ ] **BUD-02**: Real-time budget tracking with threshold warnings at 80% and overspending alerts at 100%.
- [ ] **DASH-01**: Visual dashboard with Chart.js showing category breakdown (pie/doughnut), monthly totals (line), and budget vs. actual (bar).
- [ ] **INS-01**: Deterministic rule-based insights and savings recommendations based on calculated month-over-month figures.

### Out of Scope

- **Direct Bank / SMS Integration**: Excluded for initial mini-project scope due to privacy/telecom API complexities.
- **Payment Processing / UPI Transfer Execution**: App is an information and tracking system, not a payment gateway.
- **Receipt Image OCR (Vision)**: Deferred to future enhancements (Phase 2 / v2) to prioritize offline zero-cost scikit-learn stack.
- **Multi-currency / Multi-language**: Initial v1 targets Indian Rupee (₹) and English.

## Context

- Designed as an AI-Based Information System mini-project adhering to a 3-layer architecture: Presentation (HTML/CSS/JS/Chart.js), Application (Python Flask), and Data (SQLite + model.joblib).
- Eliminates context-drift and calculation errors by computing all math strictly in Python/SQL, utilizing ML strictly for NLP categorization.
- Machine learning model is trained on a curated ~300-item dataset across 8 categories: Food, Travel, Shopping, Bills, Entertainment, Health, Education, Other.

## Constraints

- **Tech Stack**: Python 3.10+, Flask, SQLite, scikit-learn, joblib, HTML/CSS/JavaScript, Chart.js.
- **Offline / Zero-Cost AI**: No paid cloud LLM APIs; model inference must run locally in under 1 second.
- **Accuracy & Reliability**: Mathematical calculations (totals, percentages, remaining budgets) are deterministic code, never hallucinated by ML.
- **Performance**: Web pages must load in under 2 seconds.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Flask + SQLite + Vanilla JS | Lightweight, serverless single-file DB, perfect fit for mini-project architecture | ✓ Good |
| scikit-learn TF-IDF + Logistic Regression | Runs completely offline, fast (<50ms), achieves >85% accuracy on short expense strings | ✓ Good |
| Rule-based Insight Generation | Prevents AI hallucination in financial math; outputs reliable, data-grounded observations | ✓ Good |

---
*Last updated: 2026-10-23 after /gsd-new-project initialization*
