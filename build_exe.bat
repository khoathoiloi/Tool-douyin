@echo off
title Build Douyin Video Extractor to EXE
cd /d "%~dp0"
echo ========================================================
echo   BAT DAU DONG GOI UNG DUNG RA FILE .EXE CHO WINDOWS
echo ========================================================
echo.

echo Dang kiem tra thu vien PyInstaller...
python -m pip install pyinstaller customtkinter pillow openpyxl pandas requests

echo.
echo Dang dong goi... Vui long doi trong giay lat...
pyinstaller --noconfirm --onedir --windowed ^
    --name "DouyinVideoExtractor" ^
    --add-data "config.json;." ^
    --add-data "core;core" ^
    --add-data "gui;gui" ^
    --collect-all customtkinter ^
    main.py

echo.
if exist "dist\DouyinVideoExtractor\DouyinVideoExtractor.exe" (
    echo ========================================================
    echo   DONG GOI THANH CONG!
    echo   File chay: dist\DouyinVideoExtractor\DouyinVideoExtractor.exe
    echo ========================================================
) else (
    echo [LOI] Dong goi that bai. Vui long kiem tra log o tren!
)
pause
