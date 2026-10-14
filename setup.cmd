@echo off
rem One-time setup without Docker (start.cmd also runs this automatically on first use).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-local.ps1" %*
if errorlevel 1 pause
