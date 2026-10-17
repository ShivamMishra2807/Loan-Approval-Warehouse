import os
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[2]
load_dotenv(ROOT/".env")
def envpath(key, default):
    p=Path(os.getenv(key, str(default)))
    return p if p.is_absolute() else ROOT/p
CSV_PATH=envpath("LN_CSV_PATH","data/raw/loan_approval_dataset.csv")
REPORT_DIR=envpath("LN_REPORT_DIR","reports")
MODEL_DIR=envpath("LN_MODEL_DIR","models")
DSN=os.getenv("LN_DSN","")
SEED=int(os.getenv("LN_RANDOM_SEED","42"))
WEB_DIR=ROOT/"web"
