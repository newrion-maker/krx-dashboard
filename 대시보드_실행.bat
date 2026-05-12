@echo off
chcp 65001 > nul
echo ==========================================
echo    대시보드 서버를 시작합니다...
echo    (이 창을 닫으면 대시보드가 열리지 않습니다)
echo ==========================================
echo.
start http://localhost:8000/index.html
python -m http.server 8000
pause
