@echo off
title MicroJava Compiler - CS-471L
color 0B

echo ====================================================================
echo   MicroJava Compiler - CS-471L Compiler Construction Lab
echo   UET Lahore, Spring 2026
echo ====================================================================
echo.

:: Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

set PROJ_DIR=%~dp0
cd /d "%PROJ_DIR%"

:: Install dependencies if needed
if not exist "%PROJ_DIR%requirements.txt" goto :skip_deps
if exist "%PROJ_DIR%venv\Scripts\python.exe" (
    set PYTHON=%PROJ_DIR%venv\Scripts\python.exe
    goto :deps_done
)

echo [INFO] Installing dependencies...
pip install -r requirements.txt >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] pip install failed. Trying flask directly...
    pip install flask>=3.0.0 >nul 2>&1
)
:deps_done
:deps_done_skip
if "%PYTHON%"=="" set PYTHON=python

echo [INFO] Dependencies ready.
echo.

:: If no arguments, show menu
if "%1"=="" goto :menu
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help
if "%1"=="/?" goto :help

:: Run specific module
%PYTHON% main.py %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Compilation failed. See output above.
    pause
)
exit /b %ERRORLEVEL%

:menu
cls
echo ====================================================================
echo   MicroJava Compiler - CS-471L
echo   Interactive Menu
echo ====================================================================
echo.
echo  Available commands:
echo.
echo   1. Run Lexical Analyzer
echo   2. Run Recursive Descent Parser
echo   3. Run LL(1) Predictive Parser
echo   4. Run LR Parser (SLR(1))
echo   5. Run Symbol Table Manager
echo   6. Run Full Compilation Pipeline
echo   7. Show Grammar, FIRST/FOLLOW Sets, and Parsing Tables
echo   8. Interactive Mode (type code manually)
echo   9. Launch Web UI (Flask)
echo  10. Run ALL test files through ALL modules
echo  11. Install dependencies
echo.
echo  R. Run specific module (enter custom module and file)
echo  H. Help
echo  Q. Quit
echo.
set /p choice="  Enter your choice (1-11, R, H, Q): "

if "%choice%"=="1" (
    call :pick_file "lexer"
    goto :end
) else if "%choice%"=="2" (
    call :pick_file "recursive"
    goto :end
) else if "%choice%"=="3" (
    call :pick_file "ll1"
    goto :end
) else if "%choice%"=="4" (
    call :pick_file "lr"
    goto :end
) else if "%choice%"=="5" (
    call :pick_file "symbol_table"
    goto :end
) else if "%choice%"=="6" (
    call :pick_file "full"
    goto :end
) else if "%choice%"=="7" (
    cls
    echo ====================================================================
    echo   Grammar, FIRST/FOLLOW Sets, and Parsing Tables
    echo ====================================================================
    echo.
    %PYTHON% main.py grammar
    echo.
    pause
    goto :menu
) else if "%choice%"=="8" (
    cls
    %PYTHON% main.py interactive
    echo.
    pause
    goto :menu
) else if "%choice%"=="9" (
    cls
    echo ====================================================================
    echo   Launching Web UI...
    echo ====================================================================
    echo.
    echo  Open your browser to: http://127.0.0.1:5000
    echo  Press CTRL+C to quit.
    echo.
    %PYTHON% app.py
    pause
    goto :menu
) else if "%choice%"=="10" (
    call :run_all_tests
    goto :end
) else if /i "%choice%"=="R" (
    call :run_custom
    goto :end
) else if /i "%choice%"=="H" (
    goto :help
) else if /i "%choice%"=="Q" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice.
    timeout /t 2 >nul
    goto :menu
)

:pick_file
set MODULE=%1
cls
echo ====================================================================
echo   Select source file for %MODULE%
echo ====================================================================
echo.
echo  Available test files:
echo.
setlocal enabledelayedexpansion
set idx=0
for %%f in ("%PROJ_DIR%test\*.mj") do (
    set /a idx+=1
    set "file[!idx!]=%%~nxf"
    echo  !idx!. %%~nxf
)
if !idx!==0 (
    echo  (no .mj files found in test\ folder)
    echo.
    echo  Enter a file path manually:
    set /p manual_path="  File path: "
    if "!manual_path!"=="" goto :menu
    %PYTHON% main.py !MODULE! "!manual_path!"
    echo.
    pause
    goto :menu
)
echo.
echo  M. Manual (enter your own file path)
echo  B. Back to menu
echo.
set /p fp_idx="  Enter file number: "
if "!fp_idx!"=="" goto :menu
if /i "!fp_idx!"=="B" goto :menu
if /i "!fp_idx!"=="M" (
    set /p manual_path="  File path: "
    if "!manual_path!"=="" goto :menu
    %PYTHON% main.py !MODULE! "!manual_path!"
    echo.
    pause
    goto :menu
)
set "selected_file=!file[%fp_idx%]!"
if "!selected_file!"=="" (
    echo Invalid selection.
    timeout /t 2 >nul
    goto :menu
)
%PYTHON% main.py !MODULE! "!selected_file!"
echo.
pause
goto :menu
endlocal

:run_all_tests
cls
echo ====================================================================
echo   Running ALL test files through ALL modules...
echo ====================================================================
echo.
setlocal enabledelayedexpansion
for %%f in ("%PROJ_DIR%test\*.mj") do (
    echo.
    echo ====================================================================
    echo   Testing: %%~nxf
    echo ====================================================================
    echo.
    echo  [LEXER]
    %PYTHON% main.py lexer "%%f" 2>&1
    echo.
    echo  [RECURSIVE DESCENT]
    %PYTHON% main.py recursive "%%f" 2>&1
    echo.
    echo  [LL(1)]
    %PYTHON% main.py ll1 "%%f" 2>&1
    echo.
    echo  [LR PARSER]
    %PYTHON% main.py lr "%%f" 2>&1
    echo.
    echo  [SYMBOL TABLE]
    %PYTHON% main.py symbol_table "%%f" 2>&1
    echo.
    echo  [FULL COMPILATION]
    %PYTHON% main.py full "%%f" 2>&1
    echo.
    echo  -----------------------------------------
    echo   Done with %%~nxf
    echo  -----------------------------------------
)
echo.
echo  All tests completed!
echo.
pause
goto :menu
endlocal

:run_custom
cls
echo ====================================================================
echo   Custom Run
echo ====================================================================
echo.
echo  Enter module (lexer, recursive, ll1, lr, symbol_table, full):
set /p cmod="  Module: "
echo  Enter source file path (or just filename from test\ folder):
set /p cfile="  File: "
if "%cmod%"=="" (
    echo Module cannot be empty.
    timeout /t 2 >nul
    goto :menu
)
%PYTHON% main.py %cmod% "%cfile%"
echo.
pause
goto :menu

:help
cls
echo ====================================================================
echo   MicroJava Compiler - Help
echo ====================================================================
echo.
echo  USAGE:
echo    run.bat <module> [source_file]
echo.
echo  MODULES:
echo    lexer         - Run lexical analyzer on source file
echo    recursive     - Run recursive descent parser
echo    ll1           - Run LL(1) predictive parser
echo    lr            - Run LR parser (SLR(1))
echo    symbol_table  - Run symbol table manager
echo    full          - Run full compilation pipeline
echo    grammar       - Show grammar, FIRST/FOLLOW, parsing tables
echo    interactive   - Interactive mode (type code manually)
echo.
echo  EXAMPLES:
echo    run.bat lexer test\test_simple.mj
echo    run.bat full test_simple.mj
echo    run.bat ll1 test1_valid.mj
echo    run.bat grammar
echo    run.bat interactive
echo    run.bat            (shows interactive menu)
echo.
echo  WEB UI:
echo    run.bat            -> then choose option 9 (Launch Web UI)
echo    or simply run: python app.py
echo.
echo  NOTES:
echo    - Files are searched in test\ folder automatically
echo    - You can also provide full paths to .mj files
echo    - Install dependencies: run.bat -> option 11
echo.
pause
goto :menu

:end
echo.
