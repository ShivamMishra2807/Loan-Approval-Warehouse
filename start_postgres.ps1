$pgsqlBin = "C:\Users\shivam\.gemini\antigravity\scratch\pgsql\bin"
$pgsqlData = "C:\Users\shivam\.gemini\antigravity\scratch\pgsql\data"
$pgsqlLog = "C:\Users\shivam\.gemini\antigravity\scratch\pgsql\server.log"

Write-Host "Starting PostgreSQL server on port 5432..." -ForegroundColor Cyan
& "$pgsqlBin\pg_ctl.exe" -D "$pgsqlData" -l "$pgsqlLog" start
Write-Host "PostgreSQL started successfully!" -ForegroundColor Green
