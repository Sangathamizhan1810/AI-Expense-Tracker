@echo off
setlocal enabledelayedexpansion
title Stop ExpenseAI - AI-Based Expense Tracker
color 0C

echo ================================================================
echo           Stopping ExpenseAI Server
echo ================================================================
echo.

set "FOUND=0"

:: 1. Search for any process listening on port 5000
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000" ^| findstr "LISTENING"') do (
    set "PID=%%a"
    if defined PID (
        if not "!PID!"=="0" (
            set "FOUND=1"
            echo [INFO] Found process on port 5000 ^(PID: !PID!^)
            echo [INFO] Terminating process !PID!...
            taskkill /F /PID !PID! >nul 2>&1
            if !ERRORLEVEL! equ 0 (
                echo [OK] Successfully stopped process !PID!.
            ) else (
                echo [WARN] Could not terminate process !PID!.
            )
        )
    )
)

:: 2. Also close any cmd window titled "ExpenseAI*"
taskkill /F /FI "WINDOWTITLE eq ExpenseAI*" >nul 2>&1

echo.
if "!FOUND!"=="1" (
    echo [OK] ExpenseAI server has been stopped.
) else (
    echo [INFO] No active process was listening on port 5000.
    echo [INFO] Server is already stopped.
)

echo.
:: Clean pause compatible with redirected streams
ping 127.0.0.1 -n 3 >nul
exit /b 0
