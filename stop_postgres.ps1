$pgsqlBin = "C:\Users\shivam\.gemini\antigravity\scratch\pgsql\bin"
$pgsqlData = "C:\Users\shivam\.gemini\antigravity\scratch\pgsql\data"

Write-Host "Stopping PostgreSQL server..." -ForegroundColor Yellow
& "$pgsqlBin\pg_ctl.exe" -D "$pgsqlData" stop
Write-Host "PostgreSQL stopped." -ForegroundColor Green
