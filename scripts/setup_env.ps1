$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -e .
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests

Write-Host ""
Write-Host "Environment ready."
Write-Host "Interpreter: $projectRoot\.venv\Scripts\python.exe"
Write-Host "Run demo: .\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm auto"
