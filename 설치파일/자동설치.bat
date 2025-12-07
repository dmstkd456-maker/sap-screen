@echo off
chcp 65001 >nul
echo ========================================
echo   SAP 데이터 포털 자동 설치
echo ========================================
echo.

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo Python 설치 방법:
    echo 1. https://www.python.org/downloads/ 접속
    echo 2. Python 3.11 이상 다운로드
    echo 3. 설치 시 "Add Python to PATH" 반드시 체크!
    echo.
    pause
    exit /b 1
)

echo [확인] Python 설치됨
python --version
echo.

REM 필요 패키지 설치
echo [설치] 필요한 패키지를 설치합니다...
echo.
pip install flask pandas openpyxl python-dateutil

if errorlevel 1 (
    echo.
    echo [오류] 패키지 설치 실패
    echo python -m pip install flask pandas openpyxl python-dateutil 로 다시 시도해보세요.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   설치 완료!
echo ========================================
echo.
echo 실행 방법:
echo   SAP포털실행.bat 더블클릭
echo   또는 python app.py 실행 후
echo   http://localhost:5001 접속
echo.
pause
