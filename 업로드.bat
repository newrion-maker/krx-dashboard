@echo off
echo [1/3] 서버의 최신 데이터를 가져옵니다...
git pull --rebase origin main

echo [2/3] 수정한 코드를 업로드 준비합니다...
git add .
git commit -m "fix: sk hynix ranking logic"

echo [3/3] 서버로 업로드를 시작합니다...
git push origin main

echo ========================================
echo 업로드가 완료되었습니다. GitHub Actions에서 결과를 확인하세요!
echo ========================================
pause
