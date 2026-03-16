#!/usr/bin/env powershell
# Start Mini-OpenClaw Backend Server

# Get the script's directory (Project Root)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Set Python path to Project Root
$env:PYTHONPATH = $scriptDir

# Change to Project Root
Set-Location $scriptDir

Write-Host "Starting Mini-OpenClaw Backend Server..."
Write-Host "Working Directory: $(Get-Location)"
Write-Host "Python Path: $env:PYTHONPATH"

# Start the server using module syntax to ensure proper package resolution
python -m backend.app
