@echo off
echo Установка зависимостей для SoundGoodizer...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не установлен!
    echo Установите Python с официального сайта: https://python.org
    pause
    exit /b 1
)


pip --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: pip не установлен!
    echo Установите pip: python -m ensurepip --upgrade
    pause
    exit /b 1
)

echo Устанавливаем Flask...
pip install flask

echo Устанавливаем pyodbc...
pip install pyodbc

echo Устанавливаем Werkzeug...
pip install werkzeug

echo Устанавливаем flask-mail...
pip install flask-mail

echo.
echo Все зависимости успешно установлены!
echo.
pause