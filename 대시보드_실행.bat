@echo off
echo ==========================================
echo    Dashboard Server Starting...
echo    (Keep this window open)
echo ==========================================
echo.
start http://localhost:8000/주도테마_지형도.html
python -m http.server 8000
pause
