@echo off
title ExpenseAI - AI-Based Expense Tracker
color 0B

echo ================================================================
echo           ExpenseAI - AI-Based Expense Tracker
echo ================================================================
echo.

:: Navigate to project directory
cd /d "%~dp0"

:: Detect Python executable
set "PYTHON_EXE="

:: 1. Check user-specific installed Python path
if exist "C:\Users\Admin\AppData\Local\Python\bin\python.exe" (
    set "PYTHON_EXE=C:\Users\Admin\AppData\Local\Python\bin\python.exe"
    goto :PYTHON_FOUND
)

:: 2. Check standard python in PATH
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_FOUND
)

:: 3. Check Windows Python Launcher (py)
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py"
    goto :PYTHON_FOUND
)

echo [ERROR] Python was not found on your system!
echo Please ensure Python 3.10+ is installed and added to PATH.
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [OK] Using Python: %PYTHON_EXE%
echo.

:: Check if ML model exists, train if missing
if not exist "model.joblib" (
    echo [INFO] Training offline NLP machine learning model...
    "%PYTHON_EXE%" train_model.py
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to train model.
        pause
        exit /b 1
    )
    echo [OK] Model trained and saved to model.joblib
    echo.
)

:: Launch browser in background after 2 seconds
echo [INFO] Starting Flask web server at http://127.0.0.1:5000 ...
echo [INFO] Opening web browser...
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

echo.
echo ================================================================
echo Application running! Press Ctrl+C in this window to stop server.
echo ================================================================
echo.

"%PYTHON_EXE%" app.py

echo.
echo [INFO] Server stopped.
pause
