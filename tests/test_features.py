import pandas as pd
from ln.features import prepare,validate
def test_derived_features():
 d=prepare(pd.DataFrame([{"loan_id":"x","income_annum":600000,"loan_amount":1200000,"loan_term":12,"loan_status":"Approved","residential_assets_value":200000,"bank_asset_value":50000}]))
 good,bad=validate(d)
 assert len(good)==1 and len(bad)==0
 assert good.iloc[0].total_assets==250000
 assert good.iloc[0].loan_to_income==2
def test_negative_quarantined():
 d=prepare(pd.DataFrame([{"loan_id":"x","income_annum":100,"loan_amount":-1,"loan_term":12,"loan_status":"Rejected"}]))
 good,bad=validate(d)
 assert len(good)==0 and "negative_loan_amount" in bad.iloc[0].quarantine_reason
