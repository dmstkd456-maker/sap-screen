@echo off
chcp 65001 >nul
echo.
echo ================================================================================
echo              SAP 데이터 포털 - 프로그램 설치 안내
echo ================================================================================
echo.
echo 아래 프로그램들을 순서대로 설치해주세요:
echo.
echo ────────────────────────────────────────────────────────────────────────────────
echo.
echo  [1단계] Python 설치
echo      → 지금 다운로드 페이지를 엽니다
echo      → ★★★ "Add Python to PATH" 반드시 체크! ★★★
echo.
pause
start https://www.python.org/downloads/
echo.
echo  Python 설치가 완료되면 아무 키나 누르세요...
pause
echo.
echo ────────────────────────────────────────────────────────────────────────────────
echo.
echo  [2단계] Node.js 설치 (Claude Code용)
echo      → 지금 다운로드 페이지를 엽니다
echo      → LTS 버전(왼쪽 초록 버튼) 다운로드
echo.
pause
start https://nodejs.org/
echo.
echo  Node.js 설치가 완료되면 아무 키나 누르세요...
pause
echo.
echo ────────────────────────────────────────────────────────────────────────────────
echo.
echo  [3단계] 설치 확인
echo.
echo  Python 버전:
python --version 2>nul || echo   [오류] Python이 설치되지 않았거나 PATH에 없습니다!
echo.
echo  Node.js 버전:
node --version 2>nul || echo   [오류] Node.js가 설치되지 않았습니다!
echo.
echo  npm 버전:
npm --version 2>nul || echo   [오류] npm이 설치되지 않았습니다!
echo.
echo ────────────────────────────────────────────────────────────────────────────────
echo.
echo  [4단계] Claude Code 설치
echo      → 아래 명령어가 자동 실행됩니다
echo.
echo  npm install -g @anthropic-ai/claude-code
echo.
pause
npm install -g @anthropic-ai/claude-code
echo.
echo ────────────────────────────────────────────────────────────────────────────────
echo.
echo  [5단계] Python 패키지 설치
echo      → 프로젝트에 필요한 패키지를 설치합니다
echo.
pause
pip install flask pandas openpyxl python-dateutil
echo.
echo ================================================================================
echo.
echo  모든 설치가 완료되었습니다!
echo.
echo  다음 단계:
echo    1. "SAP포털실행.bat" 더블클릭 → 웹 포털 실행
echo    2. 명령 프롬프트에서 "claude" 입력 → AI 코딩 도우미 실행
echo.
echo ================================================================================
pause
