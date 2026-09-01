@echo off
title Douyin Content Finder Web Server
cd /d "%~dp0"
echo ========================================================
echo   KHOI DONG DOUYIN CONTENT FINDER WEB APPLICATION
echo ========================================================
echo.
echo Server dang khoi chay tai: http://127.0.0.1:8000
echo Mo trinh duyet (Coc Coc / Chrome / Edge) va truy cap:
echo http://127.0.0.1:8000
echo.

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
