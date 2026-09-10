@echo off
chcp 65001 >nul
title AI 定价助手

echo ========================================
echo    AI 定价助手 - 启动中
echo ========================================
echo.

REM 检查 Docker 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/3] 正在启动 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo 等待 Docker 启动...
    timeout /t 15 /nobreak >nul
) else (
    echo [1/3] Docker 已运行
)

echo.
echo [2/3] 启动应用容器...
cd /d "%~dp0"
docker-compose up -d >nul 2>&1
if %errorlevel% neq 0 (
    echo 容器启动失败，请检查 Docker Desktop 是否完全启动
    pause
    exit /b 1
)

echo 等待应用就绪...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] 打开浏览器...
start http://localhost:3000

echo.
echo ========================================
echo    启动成功！
echo    前端: http://localhost:3000
echo    后端: http://localhost:8000
echo ========================================
echo.
echo 提示：关闭本窗口不会停止应用
echo 如需停止，请运行"停止应用.bat"
echo.
timeout /t 3 /nobreak >nul
exit
