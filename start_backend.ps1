#!/usr/bin/env powershell
# Start Mini-OpenClaw Backend Server

$backendDir = "e:\miniclaw\miniclaw\backend"

# Set Python path
$env:PYTHONPATH = $backendDir

# Change to backend directory
Set-Location $backendDir

Write-Host "Starting Mini-OpenClaw Backend Server..."
Write-Host "Working Directory: $(Get-Location)"
Write-Host "Python Path: $env:PYTHONPATH"

# Start the server
python app.py
