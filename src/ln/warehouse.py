
import json
import pandas as pd

from ln.config import CSV_PATH, REPORT_DIR, ROOT, envpath
from ln.db import connect


TEXT_FIELDS = [
    "region", "state", "city", "city_tier", "loan_product", "loan_purpose",
    "application_channel", "education", "self_employed", "employment_type",
    "employer_category", "marital_status", "credit_band", "income_band",
    "amount_band", "age_band", "kyc_status", "aml_risk_band",
    "collateral_type", "decision_reason", "source_system",
    "application_year", "application_month",
]

NUM_FIELDS = [
    "income_annum", "loan_amount", "loan_term", "cibil_score",
    "total_assets", "loan_to_income", "asset_to_loan", "no_of_dependents",
    "monthly_income_inr", "existing_monthly_emi_inr", "foir_pct",
    "debt_to_income_pct", "sanctioned_amount_inr", "interest_rate_pct",
    "emi_inr", "bureau_tradelines", "credit_enquiries_3m",
    "delinquencies_12m", "dpd_30plus_count_12m",
    "cheque_or_emi_bounces_12m", "collateral_value_inr",
    "loan_to_value_pct", "employment_tenure_months",
    "bank_relationship_months", "average_monthly_balance_inr",
    "current_account_balance_inr", "age", "disbursed_flag",
    "fraud_alert_flag",
]

ALL_FIELDS = TEXT_FIELDS + NUM_FIELDS


DDL = """
CREATE TABLE IF NOT EXISTS raw_loan_application (
    loan_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    loaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS etl_run_log (
    run_id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    source_rows BIGINT,
    accepted_rows BIGINT,
    quarantined_rows BIGINT,
    status TEXT,
    details JSONB
);

CREATE TABLE IF NOT EXISTS dim_status (
    status_key BIGSERIAL PRIMARY KEY,
    loan_status TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_education (
    education_key BIGSERIAL PRIMARY KEY,
    education TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_employment_type (
    employment_key BIGSERIAL PRIMARY KEY,
    self_employed TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_credit_band (
    credit_band_key BIGSERIAL PRIMARY KEY,
    credit_band TEXT UNIQUE NOT NULL,
    risk_tier TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_region (
    region_key BIGSERIAL PRIMARY KEY,
    region TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_loan_product (
    product_key BIGSERIAL PRIMARY KEY,
    loan_product TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_loan_application (
    loan_id TEXT PRIMARY KEY,
    income_annum DOUBLE PRECISION,
    loan_amount DOUBLE PRECISION,
    loan_term DOUBLE PRECISION,
    cibil_score DOUBLE PRECISION,
    total_assets DOUBLE PRECISION,
    loan_to_income DOUBLE PRECISION,
    asset_to_loan DOUBLE PRECISION,
    credit_band TEXT,
    income_band TEXT,
    amount_band TEXT,
    education TEXT,
    self_employed TEXT,
    no_of_dependents DOUBLE PRECISION,
    loan_status TEXT NOT NULL,
    region TEXT,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    loan_product TEXT,
    loan_purpose TEXT,
    application_channel TEXT,
    employment_type TEXT,
    employer_category TEXT,
    marital_status TEXT,
    age DOUBLE PRECISION,
    age_band TEXT,
    monthly_income_inr DOUBLE PRECISION,
    existing_monthly_emi_inr DOUBLE PRECISION,
    foir_pct DOUBLE PRECISION,
    debt_to_income_pct DOUBLE PRECISION,
    sanctioned_amount_inr DOUBLE PRECISION,
    interest_rate_pct DOUBLE PRECISION,
    emi_inr DOUBLE PRECISION,
    bureau_tradelines DOUBLE PRECISION,
    credit_enquiries_3m DOUBLE PRECISION,
    delinquencies_12m DOUBLE PRECISION,
    dpd_30plus_count_12m DOUBLE PRECISION,
    cheque_or_emi_bounces_12m DOUBLE PRECISION,
    collateral_type TEXT,
    collateral_value_inr DOUBLE PRECISION,
    loan_to_value_pct DOUBLE PRECISION,
    kyc_status TEXT,
    aml_risk_band TEXT,
    fraud_alert_flag DOUBLE PRECISION,
    bank_relationship_months DOUBLE PRECISION,
    average_monthly_balance_inr DOUBLE PRECISION,
    current_account_balance_inr DOUBLE PRECISION,
    decision_reason TEXT,
    source_system TEXT,
    application_year TEXT,
    application_month TEXT,
    loaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fact_status
    ON fact_loan_application(loan_status);

CREATE INDEX IF NOT EXISTS idx_fact_credit_band
    ON fact_loan_application(credit_band);

CREATE TABLE IF NOT EXISTS fact_loan_repayment (
    repayment_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    installment_number INTEGER,
    due_date DATE,
    emi_amount DOUBLE PRECISION,
    amount_paid DOUBLE PRECISION,
    days_past_due INTEGER,
    payment_status TEXT,
    estimated_outstanding_principal DOUBLE PRECISION,
    illustrative_npa_flag BOOLEAN,
    loaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_repayment_loan
    ON fact_loan_repayment(loan_id);
"""


def pyval(value):
    """Convert pandas/numpy values to PostgreSQL-compatible Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, pd.Timestamp):
        return value.date()

    return value


def as_bool(value):
    """Safely convert common CSV boolean representations to bool."""
    if value is None or pd.isna(value):
        return None

    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()

    if normalized in ("1", "1.0", "true", "yes", "y"):
        return True

    if normalized in ("0", "0.0", "false", "no", "n"):
        return False

    return None


def main():
    with connect() as conn, conn.cursor() as cur:
        # Create warehouse tables and indexes.
        cur.execute(DDL)

        # Support databases created using the original starter schema.
        existing = {
            row[0]
            for row in cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'fact_loan_application'
                """
            ).fetchall()
        }

        text_cols = {
            column for column in TEXT_FIELDS if column not in existing
        }
        numeric_cols = {
            column for column in NUM_FIELDS if column not in existing
        }

        for column in sorted(text_cols):
            cur.execute(
                f'ALTER TABLE fact_loan_application '
                f'ADD COLUMN IF NOT EXISTS "{column}" TEXT'
            )

        for column in sorted(numeric_cols):
            cur.execute(
                f'ALTER TABLE fact_loan_application '
                f'ADD COLUMN IF NOT EXISTS "{column}" DOUBLE PRECISION'
            )

        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_fact_region "
            "ON fact_loan_application(region)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_fact_product "
            "ON fact_loan_application(loan_product)"
        )

        # Analytical views.
        cur.execute("""
            CREATE OR REPLACE VIEW vw_approval_by_credit_band AS
            SELECT
                credit_band,
                COUNT(*) AS applications,
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE loan_status = 'Approved'
                    ) / NULLIF(COUNT(*), 0),
                    2
                ) AS approval_rate_pct
            FROM fact_loan_application
            GROUP BY credit_band
        """)

        cur.execute("""
            CREATE OR REPLACE VIEW vw_approval_by_income_band AS
            SELECT
                income_band,
                COUNT(*) AS applications,
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE loan_status = 'Approved'
                    ) / NULLIF(COUNT(*), 0),
                    2
                ) AS approval_rate_pct
            FROM fact_loan_application
            GROUP BY income_band
        """)

        cur.execute("""
            CREATE OR REPLACE VIEW vw_approval_by_region AS
            SELECT
                region,
                COUNT(*) AS applications,
                COUNT(*) FILTER (
                    WHERE loan_status = 'Approved'
                ) AS approved,
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE loan_status = 'Approved'
                    ) / NULLIF(COUNT(*), 0),
                    2
                ) AS approval_rate_pct,
                ROUND(AVG(loan_amount)::numeric, 2)
                    AS average_requested_amount
            FROM fact_loan_application
            GROUP BY region
        """)

        cur.execute("""
            CREATE OR REPLACE VIEW vw_approval_by_product AS
            SELECT
                loan_product,
                COUNT(*) AS applications,
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE loan_status = 'Approved'
                    ) / NULLIF(COUNT(*), 0),
                    2
                ) AS approval_rate_pct,
                ROUND(AVG(loan_amount)::numeric, 2)
                    AS average_requested_amount
            FROM fact_loan_application
            GROUP BY loan_product
        """)

        # Load application records previously staged by the ETL process.
        cur.execute("SELECT payload FROM raw_loan_application")
        rows = [row[0] for row in cur.fetchall()]

        for record in rows:
            status = str(record.get("loan_status") or "Unknown")
            education = str(record.get("education") or "Unknown")
            self_employed = str(record.get("self_employed") or "Unknown")
            region = str(record.get("region") or "Other")
            product = str(record.get("loan_product") or "Unknown")

            cur.execute(
                """
                INSERT INTO dim_status (loan_status)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """,
                (status,),
            )

            cur.execute(
                """
                INSERT INTO dim_education (education)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """,
                (education,),
            )

            cur.execute(
                """
                INSERT INTO dim_employment_type (self_employed)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """,
                (self_employed,),
            )

            cur.execute(
                """
                INSERT INTO dim_region (region)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """,
                (region,),
            )

            cur.execute(
                """
                INSERT INTO dim_loan_product (loan_product)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """,
                (product,),
            )

            credit_band = record.get("credit_band")

            if credit_band and not pd.isna(credit_band):
                risk_tier = (
                    "Higher"
                    if credit_band in ("Low", "Fair")
                    else "Standard"
                )

                cur.execute(
                    """
                    INSERT INTO dim_credit_band (credit_band, risk_tier)
                    VALUES (%s, %s)
                    ON CONFLICT (credit_band)
                    DO UPDATE SET risk_tier = EXCLUDED.risk_tier
                    """,
                    (credit_band, risk_tier),
                )

            loan_id = record.get("loan_id")

            if loan_id is None or pd.isna(loan_id):
                raise ValueError(
                    "An application record has no loan_id. "
                    "Check the input dataset and ETL output."
                )

            values = [record.get(column) for column in ALL_FIELDS]
            names = ["loan_id"] + ALL_FIELDS + ["loan_status"]
            values = [str(loan_id)] + values + [status]

            placeholders = ",".join(["%s"] * len(names))
            quoted_names = ",".join(f'"{column}"' for column in names)
            updates = ",".join(
                f'"{column}" = EXCLUDED."{column}"'
                for column in ALL_FIELDS + ["loan_status"]
            )

            cur.execute(
                f"""
                INSERT INTO fact_loan_application ({quoted_names})
                VALUES ({placeholders})
                ON CONFLICT (loan_id)
                DO UPDATE SET {updates}
                """,
                values,
            )

        # Load repayment records, mapping the synthetic dataset's columns
        # to the warehouse schema.
        repay_path = envpath(
            "LN_REPAYMENTS_PATH",
            "data/raw/loan_repayments_monthly_synthetic.csv",
        )

        repayment_count = 0

        if repay_path.exists():
            rdf = pd.read_csv(repay_path)

            required_sources = [
                "repayment_id",
                "application_id",
                "installment_number",
                "due_date",
                "scheduled_emi_inr",
                "amount_paid_inr",
                "days_past_due",
                "payment_status",
                "outstanding_principal_estimate_inr",
                "npa_flag_90plus_dpd",
            ]

            missing = [
                column for column in required_sources
                if column not in rdf.columns
            ]

            if missing:
                raise ValueError(
                    f"Repayment CSV is missing columns: {missing}. "
                    f"File: {repay_path}"
                )

            # application_id in the repayment CSV refers to the
            # application_id in the application payload. The warehouse
            # fact table uses the corresponding loan_id.
            application_to_loan = {}

            for record in rows:
                application_id = record.get("application_id")
                loan_id = record.get("loan_id")

                if (
                    application_id is not None
                    and loan_id is not None
                    and not pd.isna(application_id)
                    and not pd.isna(loan_id)
                ):
                    application_to_loan[str(application_id)] = str(loan_id)

            rdf["loan_id"] = rdf["application_id"].map(
                lambda value: (
                    application_to_loan.get(str(value))
                    if pd.notna(value)
                    else None
                )
            )

            # Rename source fields to the warehouse's column names.
            rdf["emi_amount"] = rdf["scheduled_emi_inr"]
            rdf["amount_paid"] = rdf["amount_paid_inr"]
            rdf["estimated_outstanding_principal"] = (
                rdf["outstanding_principal_estimate_inr"]
            )
            rdf["illustrative_npa_flag"] = (
                rdf["npa_flag_90plus_dpd"].map(as_bool)
            )

            expected = [
                "repayment_id",
                "loan_id",
                "installment_number",
                "due_date",
                "emi_amount",
                "amount_paid",
                "days_past_due",
                "payment_status",
                "estimated_outstanding_principal",
                "illustrative_npa_flag",
            ]

            # Fail early with a useful error instead of inserting NULL loan IDs.
            missing_loan_ids = rdf["loan_id"].isna()

            if missing_loan_ids.any():
                examples = (
                    rdf.loc[missing_loan_ids, "application_id"]
                    .astype(str)
                    .head(5)
                    .tolist()
                )

                raise ValueError(
                    f"Could not map {int(missing_loan_ids.sum())} repayment "
                    f"rows to warehouse loan IDs. Example application_id "
                    f"values: {examples}. Check that ETL loaded the matching "
                    "application dataset into raw_loan_application."
                )

            for _, repayment in rdf[expected].iterrows():
                values = [pyval(value) for value in repayment.tolist()]

                cur.execute(
                    """
                    INSERT INTO fact_loan_repayment (
                        repayment_id,
                        loan_id,
                        installment_number,
                        due_date,
                        emi_amount,
                        amount_paid,
                        days_past_due,
                        payment_status,
                        estimated_outstanding_principal,
                        illustrative_npa_flag
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (repayment_id)
                    DO UPDATE SET
                        loan_id = EXCLUDED.loan_id,
                        installment_number = EXCLUDED.installment_number,
                        due_date = EXCLUDED.due_date,
                        emi_amount = EXCLUDED.emi_amount,
                        amount_paid = EXCLUDED.amount_paid,
                        days_past_due = EXCLUDED.days_past_due,
                        payment_status = EXCLUDED.payment_status,
                        estimated_outstanding_principal =
                            EXCLUDED.estimated_outstanding_principal,
                        illustrative_npa_flag =
                            EXCLUDED.illustrative_npa_flag
                    """,
                    values,
                )

            repayment_count = len(rdf)

    print(
        f"Warehouse loaded from {len(rows)} raw applications "
        f"and {repayment_count} repayment records."
    )


if __name__ == "__main__":
    main()

