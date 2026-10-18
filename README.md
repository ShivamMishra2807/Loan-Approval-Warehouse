# Indian Loan Intelligence Warehouse

A standalone, web-based analytics, data warehousing, OLAP, and machine-learning decision-support platform built with Python, PostgreSQL, FastAPI, and Vanilla JavaScript/CSS with Plotly.

> **Architecture:** This project is a complete, standalone web application. All dashboards, visualisations, OLAP queries, data engineering audits, and model evaluation operate natively through the browser and backend.

> **Data disclaimer:** Application and monthly repayment records are synthetic Indian loan data generated for coursework and analytics demonstrations. Repayment and NPA flags are illustrative, and model predictions must never be used for actual credit decisions.

---

## Key Platform Capabilities

1. **Executive Overview:** 6 real-time KPI metrics calculated from warehouse data, dynamic evidence-based Key Findings generator (3-5 observations with figures, sample size, interpretation, and jump links), and portfolio mix charts.
2. **Application Analytics:** Credit Band × Income Band approval heatmap matrix, loan amount percentile distributions by outcome, Loan-to-Income (LTI) leverage tiers, education, and employment comparisons.
3. **Repayment Analytics:** Surveillance of 56,447 monthly instalment records across 5,000 distinct loans, payment status distribution, DPD migration buckets (0 days, 1-30 days, 31-60 days, 61-90 days, 90+ days illustrative NPA), and monthly cash flow trends.
4. **Data Quality & ETL:** Visual pipeline architecture diagram (CSV Ingestion ➔ 12 Validation Rules ➔ Feature Derivation ➔ JSONB Staging ➔ Dimensional Warehouse ➔ Analytics), completeness metrics (96.34%), quarantine logs, and full `etl_run_log` execution audit history.
5. **Warehouse Explorer:** Interactive Star-Schema and Snowflake-Schema diagrams with cardinalities and primary/foreign key mappings, searchable and paginated live record browser across all warehouse tables, schema comparisons, and interactive data dictionary.
6. **SQL & OLAP Analytics:** Multi-dimensional OLAP studio supporting Roll-up, Drill-down, Slice, Dice, and Pivot cross-tabulations across 12 dimensions and 6 measures, with formatted executed SQL queries and automated natural-language analytical explanations.
7. **Customer Segmentation:** Unsupervised K-Means clustering (k=4) trained on applicant financials, leverage, and credit score distributions. Non-judgmental profiles with average income, loan amount, assets, and approval rates.
8. **Model Analytics:** Unified model comparison scorecard (Logistic Regression, Decision Tree, Random Forest) across Accuracy, Precision, Recall, F1, and ROC-AUC. Confusion matrix heatmap, Random Forest feature importance rankings, and searchable/paginated test predictions explorer with CSV export.
9. **Interactive Prediction Lab:** Real-time applicant underwriting simulator powered by the trained Random Forest model with presets, approval probability meter, and applicant driving factor explanations.
10. **Methodology & Governance:** Comprehensive documentation covering dataset provenance, ETL logic, dimensional star-schema design, OLAP queries, ML leakage mitigation, and ethical lending limitations.

---

## Included Data

- `data/raw/loan_applications_india_synthetic.csv` — 5,000 synthetic applications with Indian loan attributes.
- `data/raw/loan_repayments_monthly_synthetic.csv` — 56,447 synthetic monthly repayment observations.
- `data/reference/dim_branch.csv` and `dim_loan_product.csv` — reference lookup dimensions.
- `data/reference/regional_summary.csv` — precomputed regional benchmark summary.

---

## Setup & Execution (Windows PowerShell)

```powershell
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Set PYTHONPATH to src
$env:PYTHONPATH = "src"

# 3. Ingest CSV data into warehouse (if not already loaded)
python -m ln.etl_loans
python -m ln.warehouse
python -m ln.eda

# 4. Train baseline models & customer segmentation
python -m ln.mining

# 5. Launch FastAPI Application Server
python -m uvicorn ln.api:app --host 127.0.0.1 --port 8078 --reload
```

Open `http://127.0.0.1:8078` in your browser to access the complete Analytics Platform, and `http://127.0.0.1:8078/docs` for the OpenAPI interactive documentation.

---

## Deploy to Vercel

The project includes built-in Vercel configuration via [`vercel.json`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/vercel.json) and [`api/index.py`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/api/index.py).

For a complete step-by-step setup guide with cloud database instructions, see **[DEPLOY_VERCEL.md](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/DEPLOY_VERCEL.md)**.

**Quick Settings for Vercel Import:**
- **Framework Preset**: `Other`
- **Root Directory**: `./` (Do **not** choose `src`)
- **Build / Output / Install Commands**: Leave default / blank (toggles OFF)
- **Environment Variables**:
  - `LN_DSN`: `postgresql://...` (Cloud PostgreSQL instance such as Neon.tech or Supabase)
  - `LN_REPORT_DIR`: `reports`
  - `LN_MODEL_DIR`: `models`
  - `LN_RANDOM_SEED`: `42`

---

## Warehouse Star Schema

The PostgreSQL warehouse implements a Star Schema centered on `fact_loan_application` with 55 attributes, accompanied by an accumulating periodic fact table `fact_loan_repayment`:

- **Fact Tables:**
  - `fact_loan_application` (PK: `loan_id`, 5,000 records)
  - `fact_loan_repayment` (PK: `repayment_id`, FK: `loan_id`, 56,447 records)
- **Lookup Dimensions:**
  - `dim_region` (PK: `region_key`)
  - `dim_loan_product` (PK: `product_key`)
  - `dim_credit_band` (PK: `credit_band_key`)
  - `dim_education` (PK: `education_key`)
  - `dim_employment_type` (PK: `employment_key`)
  - `dim_status` (PK: `status_key`)
- **Staging & Logging:**
  - `raw_loan_application` (JSONB raw ingestion storage)
  - `etl_run_log` (Execution timestamps, row counts, and status)

---

## Troubleshooting

- `Database connection error`: Verify PostgreSQL is running locally, the `loan_warehouse` database exists, and `LN_DSN` in `.env` is accurate.
- `ModuleNotFoundError: No module named 'ln'`: Run `$env:PYTHONPATH = "src"` in your PowerShell session.
- `Model not trained`: Run `python -m ln.mining` to generate `models/loan_approval_model.joblib` and metrics exports.

This is an educational analytics and decision-support system, not a production credit underwriting engine.
