@echo off
echo ============================================
echo   股票分析助手 - 安装依赖脚本
echo ============================================
echo.

:: 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] Python 未安装！请从 https://python.org 下载安装（勾选 Add to PATH）
    pause
    exit /b 1
)

:: 检查 Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] Node.js 未安装！请从 https://nodejs.org 下载安装
    pause
    exit /b 1
)

echo [1/2] 安装后端 Python 依赖...
cd /d %~dp0\backend
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [错误] 后端依赖安装失败！
    pause
    exit /b 1
)

echo [2/2] 安装前端 Node.js 依赖...
cd /d %~dp0\frontend
npm install
if %ERRORLEVEL% neq 0 (
    echo [错误] 前端依赖安装失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo   所有依赖已安装完成！
echo   请运行 start.bat 启动服务
echo ============================================
pause