import json
from decimal import Decimal
from ln.db import connect
from ln.config import REPORT_DIR

def json_safe(value):
    if isinstance(value, Decimal): return float(value)
    return str(value) if value is not None and not isinstance(value, (str, int, float, bool, list, dict)) else value

def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*),count(*) FILTER(WHERE loan_status='Approved'),avg(loan_amount),avg(cibil_score),avg(sanctioned_amount_inr) FROM fact_loan_application")
        total, approved, loan, cibil, sanctioned = cur.fetchone()
        cur.execute("SELECT loan_status,count(*) FROM fact_loan_application GROUP BY loan_status ORDER BY loan_status")
        statuses = [{"status": s, "count": n} for s, n in cur.fetchall()]
        cur.execute("SELECT credit_band,count(*),round(100.0*count(*) FILTER(WHERE loan_status='Approved')/NULLIF(count(*),0),2) FROM fact_loan_application GROUP BY credit_band ORDER BY credit_band NULLS LAST")
        bands = [{"band": b, "applications": n, "approval_rate_pct": r} for b, n, r in cur.fetchall()]
        cur.execute("SELECT COALESCE(region,'Unknown'),count(*),count(*) FILTER(WHERE loan_status='Approved'),round(100.0*count(*) FILTER(WHERE loan_status='Approved')/NULLIF(count(*),0),2),avg(cibil_score),sum(loan_amount),sum(COALESCE(sanctioned_amount_inr,0)) FROM fact_loan_application GROUP BY region ORDER BY region NULLS LAST")
        regions = [{"region": r, "applications": n, "approved": a, "approval_rate_pct": rate, "average_cibil_score": score, "requested_amount_inr": req, "sanctioned_amount_inr": san} for r,n,a,rate,score,req,san in cur.fetchall()]
        cur.execute("SELECT loan_product,count(*),round(100.0*count(*) FILTER(WHERE loan_status='Approved')/NULLIF(count(*),0),2) FROM fact_loan_application GROUP BY loan_product ORDER BY loan_product NULLS LAST")
        products = [{"loan_product": p, "applications": n, "approval_rate_pct": r} for p,n,r in cur.fetchall()]
        cur.execute("SELECT count(*),count(*) FILTER(WHERE illustrative_npa_flag IS TRUE) FROM fact_loan_repayment")
        repayment_count, illustrative_npa_count = cur.fetchone()
    out = {"total_applications": total, "approved_applications": approved,
           "approval_rate_pct": round(100*approved/total,2) if total else None,
           "average_loan_amount": float(loan) if loan is not None else None,
           "average_sanctioned_amount_inr": float(sanctioned) if sanctioned is not None else None,
           "average_cibil_score": float(cibil) if cibil is not None else None,
           "statuses": statuses, "approval_by_credit_band": bands, "approval_by_region": regions,
           "approval_by_product": products, "repayment_records": repayment_count,
           "illustrative_npa_records": illustrative_npa_count,
           "data_note": "Synthetic educational dataset; repayment/NPA measures are illustrative only."}
    (REPORT_DIR / "eda_summary.json").write_text(json.dumps(out, indent=2, default=json_safe), encoding="utf-8")
    print(json.dumps(out, indent=2, default=json_safe))

if __name__ == "__main__": main()
