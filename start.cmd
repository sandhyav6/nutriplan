@echo off
rem Starts NutriPlan without Docker: sets up on first run, starts backend + frontend, opens the browser.
rem Usage:  start.cmd            (development: hot reload)
rem         start.cmd -Production (one server, built frontend)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-local.ps1" %*
if errorlevel 1 pause
