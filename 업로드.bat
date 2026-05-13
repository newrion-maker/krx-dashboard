@echo off
chcp 65001 > nul
echo [1/3] 업데이트된 데이터를 업로드 준비합니다...
git add .
git commit -m "deploy: update market data and theme classification"

echo [2/3] 서버에서 최신 데이터를 가져옵니다...
git pull --rebase origin main

echo [3/3] 서버로 업로드를 시작합니다...
git push origin main

echo ========================================
echo 업로드가 완료되었습니다! GitHub Actions 완료 후 반영됩니다.
echo ========================================
pause
