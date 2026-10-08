@echo off
rem Turtle2Py Viz GUI launcher - double-click to start.
rem Picks the first pythonw that has plotly (the viewer needs it).
cd /d "%~dp0"
set "PYW="
for %%P in (
  "C:\Users\user\.config\openscience\data-root\conda\envs\python\pythonw.exe"
  "C:\py\p312\pythonw.exe"
) do (
  if not defined PYW if exist %%P (
    "%%~P" -c "import plotly" >nul 2>nul && set "PYW=%%~P"
  )
)
if not defined PYW (
  where pythonw >nul 2>nul && (
    pythonw -c "import plotly" >nul 2>nul && set "PYW=pythonw"
  )
)
if not defined PYW (
  echo Turtle2Py Viz needs a Python with plotly.  Install it, e.g.:
  echo     pip install plotly
  echo then double-click this file again.  Press any key...
  pause >nul
  exit /b 1
)
start "" "%PYW%" -m turtle2py.viz.app
