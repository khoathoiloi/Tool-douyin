@echo off
title Douyin Video Extractor
cd /d "%~dp0"
echo Dang khoi dong Douyin Video Extractor...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Co loi xay ra khi chay! Nhan phim bat ky de thoat...
    pause >nul
)
