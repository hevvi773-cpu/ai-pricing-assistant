@echo off
chcp 65001 >nul
title AI 定价助手 - 停止

echo 正在停止 AI 定价助手...
cd /d "%~dp0"
docker-compose down >nul 2>&1

echo.
echo ========================================
echo    应用已停止
echo ========================================
echo.
timeout /t 2 /nobreak >nul
exit
