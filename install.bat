@echo off
setlocal

echo ==============================================
echo  E-Commerce Image Processor - Windows
echo ==============================================

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py -3
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python
    ) else (
        echo Python 3 is required. Install Python 3.10+ and run this script again.
        exit /b 1
    )
)

echo [1/3] Creating virtual environment...
%PYTHON_CMD% -m venv .venv
if %ERRORLEVEL% NEQ 0 exit /b 1

echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 exit /b 1

echo [3/3] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 exit /b 1

echo.
echo Installation complete.
echo.
echo Run:
echo   python image_processor.py --list-resolutions
echo   python image_processor.py input --output output

endlocal
