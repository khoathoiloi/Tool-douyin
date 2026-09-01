@echo off
title Build Douyin Search Android APK for Galaxy S9
cd /d "%~dp0android"
echo ======================================================================
echo   DOUYIN CONTENT FINDER - ANDROID APK BUILDER (GALAXY S9 OPTIMIZED)
echo ======================================================================
echo.
echo Kiem tra moi truong Gradle va Android SDK...
if exist "gradlew.bat" (
    call gradlew.bat assembleRelease
    echo.
    echo Build hoan tat! File APK nam tai:
    echo android/app/build/outputs/apk/release/app-release.apk
) else (
    echo Ban co the mo thu muc 'android' truc tiep trong Android Studio
    echo de build file APK cai dat len Samsung Galaxy S9!
)
pause
