import json,time
import pandas as pd
from ln.config import CSV_PATH,REPORT_DIR
from ln.features import prepare,validate
from ln.db import connect
def main():
    t=time.time(); REPORT_DIR.mkdir(parents=True,exist_ok=True)
    if not CSV_PATH.exists(): raise FileNotFoundError(f"CSV not found: {CSV_PATH}. Add your dataset or set LN_CSV_PATH.")
    raw=pd.read_csv(CSV_PATH); df=prepare(raw); good,bad=validate(df)
    bad.to_csv(REPORT_DIR/"quarantine.csv",index=False)
    q={"source_rows":len(raw),"accepted_rows":len(good),"quarantined_rows":len(bad),
       "completeness_pct":round(float(raw.notna().mean().mean()*100),2),"unique_ids_pct":round(float(df.loan_id.nunique()/max(len(df),1)*100),2)}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS raw_loan_application(loan_id TEXT PRIMARY KEY,payload JSONB NOT NULL,loaded_at TIMESTAMPTZ DEFAULT now())")
        cur.execute("""CREATE TABLE IF NOT EXISTS etl_run_log(run_id BIGSERIAL PRIMARY KEY,started_at TIMESTAMPTZ DEFAULT now(),finished_at TIMESTAMPTZ,source_rows BIGINT,accepted_rows BIGINT,quarantined_rows BIGINT,status TEXT,details JSONB)""")
        cur.execute("INSERT INTO etl_run_log(source_rows,accepted_rows,quarantined_rows,status,details) VALUES(%s,%s,%s,'running',%s) RETURNING run_id",(len(raw),len(good),len(bad),json.dumps(q)))
        run=cur.fetchone()[0]
        for _,r in good.iterrows():
            payload={k:(None if pd.isna(v) else v.item() if hasattr(v,"item") else v) for k,v in r.to_dict().items()}
            cur.execute("INSERT INTO raw_loan_application(loan_id,payload) VALUES(%s,%s) ON CONFLICT(loan_id) DO UPDATE SET payload=EXCLUDED.payload,loaded_at=now()",(str(r.loan_id),json.dumps(payload,default=str)))
        cur.execute("UPDATE etl_run_log SET finished_at=now(),status='success' WHERE run_id=%s",(run,))
    q.update({"run_id":run,"duration_seconds":round(time.time()-t,3),"quarantine_file":str(REPORT_DIR/"quarantine.csv")})
    (REPORT_DIR/"data_quality.json").write_text(json.dumps(q,indent=2))
    print(json.dumps(q,indent=2))
if __name__=="__main__": main()
