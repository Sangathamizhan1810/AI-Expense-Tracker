# Roadmap: AI-Based Expense Tracker

## Overview

A phased journey to build the AI-Based Expense Tracker information system from foundational database architecture and authentication to a trained offline machine learning classifier, budget alert engine, interactive Chart.js analytics dashboard, and automated spending insights.

## Phases

- [x] **Phase 1: Foundation, Database Architecture & Authentication** - Flask application skeleton, SQLite schema, secure password hashing, and user authentication flow.
- [x] **Phase 2: Core Expense Management & Export** - CRUD operations for expenses, category mapping, search/filter, and CSV export.
- [x] **Phase 3: NLP & Machine Learning Categorization** - Labelled training dataset, scikit-learn TF-IDF + Logistic Regression classifier pipeline, regex amount extraction, and sentence-based expense entry.
- [ ] **Phase 4: Budget Management & Alert Engine** - Monthly category budget setup, real-time threshold computation, 80% warning alerts, and 100% overspending notifications.
- [ ] **Phase 5: Interactive Visual Analytics Dashboard** - Financial summary KPIs and Chart.js visualizations (Category Doughnut, Monthly Trend Line, Budget vs. Actual Bar).
- [ ] **Phase 6: Spending Insights Engine, UAT & Documentation** - Deterministic rule-based insights, savings tips, comprehensive test case verification (Cases 1–13), and Mermaid architectural diagrams.

---

## Phase Details

### Phase 1: Foundation, Database Architecture & Authentication
**Goal**: Establish the core Flask environment, SQLite database structure (`users`, `categories`, `expenses`, `budgets`), responsive navigation layout, and complete registration/login/logout flow.  
**Depends on**: Nothing (first phase)  
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04  
**Success Criteria**:
  1. User can register with name, email, and password, receiving validation errors on invalid inputs.
  2. Passwords are securely hashed before database persistence.
  3. User can log in and out, with sessions securely isolated per user.
  4. Base responsive layout with modern navigation is established.  
**Plans**: 2 plans

Plans:
- [x] 01-01: Flask app structure, SQLite models, database migrations/seeders for 8 core categories.
- [x] 01-02: Authentication routes, registration/login forms with modern CSS styling, session management, and auth guards.

---

### Phase 2: Core Expense Management & Export
**Goal**: Provide full expense lifecycle management with manual entry, categorized tables, date/category filtering, and CSV export.  
**Depends on**: Phase 1  
**Requirements**: EXP-01, EXP-02, EXP-03, EXP-04, EXP-05, EXP-06  
**Success Criteria**:
  1. User can add an expense with amount (₹), date, category, and optional notes.
  2. User can view an expense list, update existing records, and delete records with confirmation.
  3. Filter bar filters entries by date range and category dynamically.
  4. User can download a clean CSV file containing their expense data.  
**Plans**: 2 plans

Plans:
- [x] 02-01: Expense CRUD routes and interactive forms with real-time field validation.
- [x] 02-02: Expense table view, category/date filtering, and CSV export endpoint.

---

### Phase 3: NLP & Machine Learning Categorization
**Goal**: Enable friction-free expense logging by entering natural language sentences (e.g. "Swiggy 250"), parsed via regex and categorized via a trained offline scikit-learn model.  
**Depends on**: Phase 2  
**Requirements**: NLP-01, NLP-02, NLP-03, NLP-04, NLP-05  
**Success Criteria**:
  1. Model training script (`train_model.py`) trains on 300+ labelled expense items across 8 categories, reaching $\ge 85\%$ test accuracy.
  2. Trained model pipeline is serialized to `model.joblib`.
  3. Sentence parser extracts numeric amount and predicts category with confidence score.
  4. If confidence $< 0.5$ or amount is missing, falls back to "Other" and prompts user confirmation.
  5. One-click natural language input UI integrated into the application.  
**Plans**: 2 plans

Plans:
- [x] 03-01: Curate dataset, build and evaluate scikit-learn TF-IDF + Logistic Regression pipeline, and generate `model.joblib`.
- [x] 03-02: Build regex amount extractor, prediction API endpoint, and natural language expense quick-add UI.

---

### Phase 4: Budget Management & Alert Engine
**Goal**: Allow users to set monthly spending limits per category and receive proactive warnings before and when overspending occurs.  
**Depends on**: Phase 2  
**Requirements**: BUD-01, BUD-02, BUD-03, BUD-04  
**Success Criteria**:
  1. User can allocate monthly budget limits for any of the 8 categories.
  2. Real-time spend is calculated from recorded expenses for the active month.
  3. Progress bars visually show budget consumption.
  4. Warning badge is triggered at 80% utilization; critical alert is shown when exceeding 100%.  
**Plans**: 1 plan

Plans:
- [ ] 04-01: Budget allocation routes, database queries, budget tracking views, and threshold alert badges.

---

### Phase 5: Interactive Visual Analytics Dashboard
**Goal**: Deliver a comprehensive financial dashboard with interactive Chart.js visualizations and key spending indicators.  
**Depends on**: Phase 2, Phase 4  
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04  
**Success Criteria**:
  1. Dashboard displays high-level financial metric cards (Total Month Spend, Budget Remaining, Top Category).
  2. Category breakdown Donut chart displays spend percentages.
  3. Monthly spending trajectory Line chart plots trends over time.
  4. Budget vs. Actual Bar chart provides direct visual comparison per category.  
**Plans**: 1 plan

Plans:
- [ ] 05-01: Dashboard aggregate data API, Chart.js integration, KPI cards, and responsive chart layout.

---

### Phase 6: Spending Insights Engine, UAT & Documentation
**Goal**: Generate automated rule-based spending insights, verify all 13 test cases from the project specification, and produce Mermaid diagrams for the project report.  
**Depends on**: Phase 3, Phase 5  
**Requirements**: INS-01, INS-02, INS-03, INS-04  
**Success Criteria**:
  1. Deterministic insights compare current month vs. prior month (e.g. "Food spending is 40% higher than last month").
  2. Personalized saving suggestions generated based on over-budget categories.
  3. Gracefully shows "Not enough data yet" for new users.
  4. All 13 test cases from documentation pass successfully.
  5. Architecture, Level-0 DFD, and ER diagrams generated in Mermaid.  
**Plans**: 2 plans

Plans:
- [ ] 06-01: Spending insights engine and UI cards with month-over-month calculation logic.
- [ ] 06-02: Comprehensive test suite verification (Cases 1–13), report documentation artifacts, and Mermaid diagrams.

---

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|---|---|---|---|
| 1. Foundation, Database & Auth | 0/2 | Not started | - |
| 2. Core Expense Management | 0/2 | Not started | - |
| 3. NLP & ML Categorization | 0/2 | Not started | - |
| 4. Budget & Alert Engine | 0/1 | Not started | - |
| 5. Interactive Analytics Dashboard | 0/1 | Not started | - |
| 6. Insights Engine & Verification | 0/2 | Not started | - |
