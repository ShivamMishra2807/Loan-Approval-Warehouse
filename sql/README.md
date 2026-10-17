The idempotent warehouse DDL is maintained in `src/ln/warehouse.py` and is applied by `python -m ln.warehouse`.

Main tables:
- `raw_loan_application`: original application payload as JSONB.
- `fact_loan_application`: application-level fact with region, state, product, channel, credit, income, and risk fields.
- `fact_loan_repayment`: monthly repayment-level fact.
- `dim_status`, `dim_education`, `dim_employment_type`, `dim_credit_band`, `dim_region`, `dim_loan_product`: lookup dimensions.

Views include approval rates by credit band, income band, region, and loan product. The schema upgrade adds new columns to an older starter database without dropping its tables.
