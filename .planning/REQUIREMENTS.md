# Requirements: AI-Based Expense Tracker

**Defined:** 2026-10-23  
**Core Value:** Frictionless expense logging through natural language sentence parsing and automatic categorization, coupled with exact budget enforcement and rule-based financial guidance—without requiring paid APIs or an active internet connection.

## v1 Requirements

### Authentication & User Isolation

- [x] **AUTH-01**: User can register securely with name, email, and password.
- [x] **AUTH-02**: Passwords are securely hashed using Werkzeug / bcrypt before storage.
- [x] **AUTH-03**: User can log in and out, with session maintained across requests.
- [x] **AUTH-04**: Complete data isolation—each user can only view, edit, or delete their own transactions, categories, and budgets.

### Expense Management

- [x] **EXP-01**: User can record an expense manually with amount (₹), date, category, and optional notes.
- [x] **EXP-02**: User can view a paginated/tabular list of all expenses with sorting by date or amount.
- [x] **EXP-03**: User can edit any previously recorded expense.
- [x] **EXP-04**: User can delete an existing expense with confirmation.
- [x] **EXP-05**: User can filter expenses by date range and category.
- [x] **EXP-06**: User can export filtered or complete expenses to a CSV file.

### AI Natural Language Categorization

- [x] **NLP-01**: Natural language entry interface accepting short sentences (e.g., "Swiggy 250", "bus ticket 30", "metro recharge 50").
- [x] **NLP-02**: Regular expression engine extracts numeric amount accurately from input strings.
- [x] **NLP-03**: Machine learning training script (`train_model.py`) trains a TF-IDF vectorizer + Logistic Regression classifier on ~300 labelled expense items across 8 categories (Food, Travel, Shopping, Bills, Entertainment, Health, Education, Other).
- [x] **NLP-04**: Classifier achieves $\ge 85\%$ test accuracy and saves pipeline as `model.joblib`.
- [x] **NLP-05**: Application inference returns predicted category with confidence score; falls back gracefully to "Other" if confidence $< 0.5$ or amount is missing, allowing manual user correction.

### Budgets & Alerts

- [x] **BUD-01**: User can set monthly spending limits for each category.
- [x] **BUD-02**: System automatically sums current month's expenses per category against the budget limit.
- [x] **BUD-03**: Visual warning badge / banner displayed when category spending reaches 80% of budget.
- [x] **BUD-04**: Critical alert triggered and highlighted when spending exceeds 100% of budget.

### Dashboard & Visualizations

- [x] **DASH-01**: Summary cards displaying total monthly spend, active budgets, remaining spend capacity, and top spending category.
- [x] **DASH-02**: Interactive Chart.js Donut/Pie chart illustrating category-wise spending distribution.
- [x] **DASH-03**: Monthly spending trend Line chart showing expense trajectory over time.
- [x] **DASH-04**: Budget vs. Actual Bar chart comparing current spend with allocated limits.

### AI Spending Insights

- [x] **INS-01**: Rule-based engine analyzes current vs. previous month spending trends per category.
- [x] **INS-02**: Generates up to three dynamic plain-language observations (e.g., "Food spending is 40% higher than last month") based strictly on calculated figures.
- [x] **INS-03**: Generates actionable savings tips based on budget utilization.
- [x] **INS-04**: Graceful state handling showing "Not enough data yet" for new accounts without prior-month history.

## v2 Requirements (Deferred)

- **V2-01**: Receipt and invoice OCR image scanning with Gemini Vision or Tesseract.
- **V2-02**: Multi-currency conversion and internationalization.
- **V2-03**: Recurring subscription tracking and renewal reminder notifications.
- **V2-04**: SMS / UPI notification parsing (mobile companion app).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Bank account API sync / Plaid | Privacy risks, API subscriptions, and beyond mini-project scope |
| Real money transfers / UPI payment processing | App is purely an informational tracking system |
| LLM API dependency (OpenAI/Claude API) | Offline constraint: must run zero-cost without internet on local scikit-learn |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| AUTH-03 | Phase 1 | Complete |
| AUTH-04 | Phase 1 | Complete |
| EXP-01 | Phase 2 | Complete |
| EXP-02 | Phase 2 | Complete |
| EXP-03 | Phase 2 | Complete |
| EXP-04 | Phase 2 | Complete |
| EXP-05 | Phase 2 | Complete |
| EXP-06 | Phase 2 | Complete |
| NLP-01 | Phase 3 | Complete |
| NLP-02 | Phase 3 | Complete |
| NLP-03 | Phase 3 | Complete |
| NLP-04 | Phase 3 | Complete |
| NLP-05 | Phase 3 | Complete |
| BUD-01 | Phase 4 | Complete |
| BUD-02 | Phase 4 | Complete |
| BUD-03 | Phase 4 | Complete |
| BUD-04 | Phase 4 | Complete |
| DASH-01 | Phase 5 | Complete |
| DASH-02 | Phase 5 | Complete |
| DASH-03 | Phase 5 | Complete |
| DASH-04 | Phase 5 | Complete |
| INS-01 | Phase 6 | Complete |
| INS-02 | Phase 6 | Complete |
| INS-03 | Phase 6 | Complete |
| INS-04 | Phase 6 | Complete |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0

---
*Requirements defined: 2026-10-23*  
*Last updated: 2026-10-23 after /gsd-new-project*
