@echo off
echo ========================================
echo   AI 定价助手 - Docker 启动
echo ========================================
echo.
echo 正在构建并启动容器（首次需要几分钟）...
echo.
docker-compose up --build -d
echo.
if %errorlevel%==0 (
    echo ========================================
    echo   启动成功！
    echo   前端: http://localhost:3000
    echo   后端: http://localhost:8000
    echo   API文档: http://localhost:8000/docs
    echo ========================================
) else (
    echo 启动失败，请检查 Docker Desktop 是否运行
)
echo.
pause
