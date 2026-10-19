@echo off
rem Installs the NHL assembly modes into VS Code (copy, no admin, no node). Run from anywhere.
setlocal
set "SRC=%~dp0nhl-asm"
set "DST=%USERPROFILE%\.vscode\extensions\nhl-disasm.nhl-asm-1.0.0"
if not exist "%SRC%\package.json" (echo Cannot find %SRC% & exit /b 1)
if exist "%USERPROFILE%\.vscode\extensions\nhl-asm" rmdir /s /q "%USERPROFILE%\.vscode\extensions\nhl-asm"
if exist "%DST%" rmdir /s /q "%DST%"
xcopy "%SRC%" "%DST%\" /e /i /q /y /exclude:%~dp0install.exclude >nul || (echo Copy failed & exit /b 1)
echo Installed to %DST%
echo Restart VS Code, then open an .asm file: the status bar should show the NHL mode.
