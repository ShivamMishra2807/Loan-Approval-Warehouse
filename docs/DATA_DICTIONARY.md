# Data dictionary and modelling notes

The default input is `data/raw/loan_applications_india_synthetic.csv`; monthly repayments are loaded from `data/raw/loan_repayments_monthly_synthetic.csv`. Both files are synthetic and for coursework/demo use only.

## Application facts
- **Identifiers and geography:** `loan_id`, `application_id`, `customer_id`, `region`, `state`, `city`, `city_tier`, `branch_id`.
- **Application context:** `application_date`, `loan_product`, `loan_purpose`, `application_channel`.
- **Applicant profile:** `age`, `marital_status`, `education`, `employment_type`, `employer_category`, `employment_tenure_months`, `no_of_dependents`, `self_employed`.
- **Income and affordability:** `monthly_income_inr`, `annual_income_inr`/`income_annum`, `existing_monthly_emi_inr`, `foir_pct`, `debt_to_income_pct`.
- **Request and terms:** `requested_loan_amount_inr`/`loan_amount`, `loan_tenure_months`/`loan_term`, `sanctioned_amount_inr`, `interest_rate_pct`, `emi_inr`.
- **Credit and risk:** `cibil_score`, `bureau_tradelines`, `credit_enquiries_3m`, `delinquencies_12m`, `dpd_30plus_count_12m`, `cheque_or_emi_bounces_12m`, `collateral_type`, `collateral_value_inr`, `loan_to_value_pct`, `kyc_status`, `aml_risk_band`, `fraud_alert_flag`.
- **Outcome:** `decision_outcome`/`loan_status`, `decision_reason`, `disbursed_flag`.
- **Derived fields:** `total_assets`, `loan_to_income`, `asset_to_loan`, `credit_band`, `income_band`, `amount_band`, `age_band`, `application_year`, `application_month`, `region` when missing.

## Validation and modelling
Required source values are annual income, requested loan amount, positive tenure, and an Approved/Rejected decision. Invalid rows are written to `reports/quarantine.csv`. The modelling script excludes outcome duplicates and post-decision fields such as decision reason, sanctioned amount, interest rate, EMI, disbursement date/flag to limit target leakage. The API demo prediction accepts the reduced legacy-compatible feature set.

## Regional split
The dataset uses a simplified coursework grouping: West, South, North, East, Central, and Other. This is an analytical mapping for this synthetic dataset, not a universal official classification.

## Repayments
`fact_loan_repayment` stores monthly synthetic repayment observations. Estimated outstanding principal and illustrative NPA flags are teaching approximations and must not be interpreted as actual bank classifications.
