$env:PYTHONPATH = "src"
Write-Host "Launching Loan Intelligence Warehouse on http://127.0.0.1:8078 ..." -ForegroundColor Cyan
python -m uvicorn ln.api:app --host 127.0.0.1 --port 8078 --reload
