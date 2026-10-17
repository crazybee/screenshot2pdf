Param(
    [string]$VenvDir = ".venv"
)

Write-Host "Creating virtual environment in $VenvDir ..."
python -m venv $VenvDir

$pip = Join-Path $VenvDir "Scripts\\pip.exe"
if (Test-Path $pip) {
    & $pip install --upgrade pip
    if (Test-Path "requirements.txt") {
        & $pip install -r requirements.txt
    } else {
        Write-Host "requirements.txt not found. Skipping package installation."
    }
    Write-Host "Virtual environment created. To activate run:`n  .\\$VenvDir\\Scripts\\Activate.ps1 (PowerShell)`n  .\\$VenvDir\\Scripts\\activate (cmd)"
} else {
    Write-Error "pip not found in virtualenv. venv creation may have failed."
}
