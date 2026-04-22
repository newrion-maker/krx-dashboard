@echo off
echo ==========================================
echo    인터넷(Github) 대시보드 업로드 중...
echo ==========================================
echo.
git add .
git commit -m "Update sector-based dashboard UI and data"
git push
echo.
echo ==========================================
echo    업로드가 완료되었습니다!
echo    인터넷 주소 반영까지 1~2분 정도 소요됩니다.
echo ==========================================
pause
