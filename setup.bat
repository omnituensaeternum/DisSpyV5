@echo off
:: Ensure Python and pip are installed
echo Checking for Python installation...
where python > nul 2> nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python first.
    exit /b
)

echo Python is installed.

:: Check if pip is installed
echo Checking for pip installation...
where pip > nul 2> nul
if %errorlevel% neq 0 (
    echo pip is not installed. Installing pip...
    python -m ensurepip --upgrade
)

echo pip is installed.

:: Create virtual environment if not already created
if not exist "DisSpy" (
    echo Creating virtual environment 'DisSpy'...
    python -m venv DisSpy
)

:: Create a folder called "data" if it doesn't exist
if not exist "data" (
    echo Creating 'data' folder...
    mkdir data
)

:: Activate the virtual environment
echo Activating the virtual environment 'DisSpy'...
call DisSpy\Scripts\activate

:: Install requirements from requirements.txt
echo Installing dependencies from requirements.txt...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Skipping dependency installation.
)

echo Setup complete!
pause
