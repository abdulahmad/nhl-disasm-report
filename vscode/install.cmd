@echo off
rem Installs the NHL assembly modes into VS Code from the packaged nhl-asm.vsix. Run from anywhere.
setlocal
where code >nul 2>nul || (echo "code" is not on PATH. In VS Code: Extensions ^> ... ^> Install from VSIX, pick %~dp0nhl-asm.vsix & exit /b 1)
code --install-extension "%~dp0nhl-asm.vsix" --force
echo.
echo Now close all editor tabs and run "Developer: Reload Window" in VS Code.
