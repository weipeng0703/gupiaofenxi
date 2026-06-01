@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   股票分析助手 - 一键启动脚本
echo ============================================
echo.

:: 项目根目录（scripts 的上级目录）
set "ROOT=%~dp0.."

:: 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] Python 未安装！请从 python.org 下载安装（勾选 Add to PATH）
    pause
    exit /b 1
)

:: 检查 Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] Node.js 未安装！请从 nodejs.org 下载安装
    pause
    exit /b 1
)

echo [1/2] 启动后端服务...
start "后端服务" cmd /k "cd /d "%ROOT%\backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] 启动前端开发服务器...
start "前端服务" cmd /k "cd /d "%ROOT%\frontend" && npm run dev"

echo.
echo ============================================
echo   服务已启动！
echo   后端 API: http://localhost:8000
echo   前端页面: http://localhost:5173
echo ============================================
echo.
echo 按任意键退出此窗口（服务将继续运行）
pause >nul