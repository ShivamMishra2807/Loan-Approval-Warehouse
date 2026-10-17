import hashlib
import re
import numpy as np
import pandas as pd

ALIASES = {
    "loan_id": ["loan_id", "loanid", "id"],
    "no_of_dependents": ["no_of_dependents", "dependents"],
    "education": ["education"],
    "self_employed": ["self_employed"],
    "income_annum": ["income_annum", "annual_income", "income", "annual_income_inr"],
    "loan_amount": ["loan_amount", "requested_loan_amount_inr"],
    "loan_term": ["loan_term", "term", "loan_tenure", "loan_tenure_months"],
    "cibil_score": ["cibil_score", "credit_score", "cibil"],
    "residential_assets_value": ["residential_assets_value", "residential_assets"],
    "commercial_assets_value": ["commercial_assets_value", "commercial_assets"],
    "luxury_assets_value": ["luxury_assets_value", "luxury_assets"],
    "bank_asset_value": ["bank_asset_value", "bank_assets"],
    "loan_status": ["loan_status", "decision_outcome", "status", "approval_status"],
}
NUMERIC_COLUMNS = [
    "no_of_dependents", "income_annum", "loan_amount", "loan_term", "cibil_score",
    "residential_assets_value", "commercial_assets_value", "luxury_assets_value", "bank_asset_value",
    "monthly_income_inr", "existing_monthly_emi_inr", "foir_pct", "debt_to_income_pct",
    "sanctioned_amount_inr", "interest_rate_pct", "emi_inr", "bureau_tradelines",
    "credit_enquiries_3m", "delinquencies_12m", "dpd_30plus_count_12m", "cheque_or_emi_bounces_12m",
    "collateral_value_inr", "loan_to_value_pct", "employment_tenure_months", "bank_relationship_months",
    "average_monthly_balance_inr", "current_account_balance_inr", "age",
]

def normalise(df):
    df = df.copy()
    df.columns = [re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_") for c in df.columns]
    rename = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                # Prefer the original compatibility columns when the synthetic CSV has both aliases.
                if target not in df.columns or alias == target:
                    rename[alias] = target
                break
    return df.rename(columns=rename)

def prepare(df):
    df = normalise(df)
    missing = [c for c in ["income_annum", "loan_amount", "loan_term", "loan_status"] if c not in df]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    if "loan_id" not in df:
        df["loan_id"] = df.astype(str).apply(lambda r: hashlib.sha256("|".join(r).encode()).hexdigest()[:24], axis=1)
    for c in NUMERIC_COLUMNS:
        if c in df:
            if c in {"fraud_alert_flag", "disbursed_flag"}:
                truth_map = {"true": 1, "false": 0, "yes": 1, "no": 0, "1": 1, "0": 0}
                df[c] = df[c].astype(str).str.strip().str.lower().map(truth_map)
            else:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    df["loan_status"] = df["loan_status"].astype("string").str.lower().map({
        "approved": "Approved", "approve": "Approved", "rejected": "Rejected", "reject": "Rejected",
    }).fillna(df["loan_status"])
    # Keep model/report target consistently tied to the decision outcome.
    if "decision_outcome" in df:
        df["decision_outcome"] = df["decision_outcome"].astype("string").str.title()
    assets = [c for c in ["residential_assets_value", "commercial_assets_value", "luxury_assets_value", "bank_asset_value"] if c in df]
    for c in assets:
        df[c] = df[c].fillna(0)
    df["total_assets"] = df[assets].sum(axis=1) if assets else 0.0
    df["loan_to_income"] = np.where(df["income_annum"] > 0, df["loan_amount"] / df["income_annum"], np.nan)
    df["asset_to_loan"] = np.where(df["loan_amount"] > 0, df["total_assets"] / df["loan_amount"], np.nan)
    if "cibil_score" in df:
        df["credit_band"] = pd.cut(df["cibil_score"], [0, 549, 649, 749, 900], labels=["Low", "Fair", "Good", "Excellent"]).astype("string")
    df["income_band"] = pd.cut(df["income_annum"], [-1, 300000, 600000, 1200000, np.inf], labels=["Low", "Lower-middle", "Upper-middle", "High"]).astype("string")
    df["amount_band"] = pd.cut(df["loan_amount"], [-1, 1000000, 3000000, 6000000, np.inf], labels=["Small", "Medium", "Large", "Very large"]).astype("string")
    if "age" in df:
        df["age_band"] = pd.cut(df["age"], [0, 25, 35, 45, 60, 120], labels=["18-25", "26-35", "36-45", "46-60", "60+"]).astype("string")
    if "application_date" in df:
        dates = pd.to_datetime(df["application_date"], errors="coerce")
        df["application_year"] = dates.dt.year.astype("Int64").astype("string")
        df["application_month"] = dates.dt.month.astype("Int64").astype("string")
    if "region" not in df and "state" in df:
        region_map = {
            "Maharashtra": "West", "Gujarat": "West", "Rajasthan": "West",
            "Karnataka": "South", "Tamil Nadu": "South", "Telangana": "South", "Kerala": "South", "Andhra Pradesh": "South",
            "Delhi": "North", "Uttar Pradesh": "North", "Punjab": "North", "Haryana": "North",
            "West Bengal": "East", "Bihar": "East", "Odisha": "East", "Assam": "East", "Madhya Pradesh": "Central",
        }
        df["region"] = df["state"].map(region_map).fillna("Other")
    return df

def validate(df):
    invalid = []
    for _, r in df.iterrows():
        why = []
        for c in ["income_annum", "loan_amount", "loan_term"]:
            if pd.isna(r.get(c)): why.append("missing_or_invalid_" + c)
        for c in ["income_annum", "loan_amount", "loan_term", "residential_assets_value", "commercial_assets_value", "luxury_assets_value", "bank_asset_value"]:
            if c in df and pd.notna(r.get(c)) and r[c] < 0: why.append("negative_" + c)
        if pd.notna(r.get("loan_term")) and r["loan_term"] <= 0: why.append("nonpositive_loan_term")
        if "cibil_score" in df and pd.notna(r.get("cibil_score")) and not 300 <= r["cibil_score"] <= 900: why.append("cibil_out_of_range")
        if r.get("loan_status") not in ("Approved", "Rejected"): why.append("unknown_loan_status")
        invalid.append(";".join(sorted(set(why))))
    x = df.copy(); x["quarantine_reason"] = invalid
    bad = x[x.quarantine_reason != ""]; good = x[x.quarantine_reason == ""].drop(columns="quarantine_reason")
    dup = good.loan_id.astype(str).duplicated()
    if dup.any():
        d = good[dup].copy(); d["quarantine_reason"] = "duplicate_loan_id"
        bad = pd.concat([bad, d], ignore_index=True); good = good[~dup]
    return good, bad
