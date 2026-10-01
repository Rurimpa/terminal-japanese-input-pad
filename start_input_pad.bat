@echo off
rem Japanese input pad - double-click this file to start it.
rem Uses the Python launcher (pyw) if present, otherwise pythonw on PATH.
where pyw >nul 2>nul && (start "" pyw "%~dp0input_pad.pyw" & exit /b 0)
where pythonw >nul 2>nul && (start "" pythonw "%~dp0input_pad.pyw" & exit /b 0)
echo Python was not found. Install it first:  winget install Python.Python.3.13
pause
