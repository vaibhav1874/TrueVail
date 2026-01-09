@echo off
echo Starting TrueVail in Production Mode...

REM Set production environment variables
set FLASK_ENV=production
set FLASK_DEBUG=0

REM Navigate to backend directory and start the server
echo Starting backend server...
cd /d "%~dp0backend"
start "TrueVail Backend" cmd /c "python app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Navigate to frontend directory and start the server
echo Starting frontend server...
cd /d "%~dp0frontend"
if exist node_modules (
    echo Node modules already installed
) else (
    echo Installing node modules...
    npm install express
)

echo Starting frontend server...
start "TrueVail Frontend" cmd /c "npx http-server -p 3000"

echo.
echo TrueVail is now running in production mode!
echo Backend: http://localhost:5001
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause >nul