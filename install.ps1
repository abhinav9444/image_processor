$ErrorActionPreference = "Stop"

Write-Host "=============================================="
Write-Host " E-Commerce Image Processor - PowerShell"
Write-Host "=============================================="

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $pythonCommand = "py"
    $pythonArgs = @("-3")
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python 3.10+ is required."
    }
    $pythonCommand = "python"
    $pythonArgs = @()
}

Write-Host "[1/3] Creating virtual environment..."
& $pythonCommand @pythonArgs -m venv .venv

Write-Host "[2/3] Activating virtual environment..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "[3/3] Installing dependencies..."
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Installation complete."
Write-Host ""
Write-Host "Run:"
Write-Host "  .\.venv\Scripts\python.exe image_processor.py --list-resolutions"
Write-Host "  .\.venv\Scripts\python.exe image_processor.py input --output output"
