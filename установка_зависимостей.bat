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

echo Устанавливаем Flask==3.0.3...
pip install Flask==3.0.3

echo Устанавливаем psycopg2-binary==2.9.9...
pip install psycopg2-binary==2.9.9

echo Устанавливаем Flask-Mail==0.10.0...
pip install Flask-Mail==0.10.0

echo Устанавливаем Werkzeug==3.0.3...
pip install Werkzeug==3.0.3

echo Устанавливаем dnspython==2.6.1...
pip install dnspython==2.6.1

echo Устанавливаем gunicorn==22.0.0...
pip install gunicorn==22.0.0

echo Устанавливаем resend==2.10.0...
pip install resend==2.10.0

echo Устанавливаем python-dotenv==1.0.1...
pip install python-dotenv==1.0.1

echo Устанавливаем Flask-Limiter==3.8.0...
pip install Flask-Limiter==3.8.0

echo Устанавливаем python-magic-bin==0.4.14...
pip install python-magic-bin==0.4.14

echo Устанавливаем openpyxl==3.1.5...
pip install openpyxl==3.1.5

echo.
echo Все зависимости успешно установлены!
echo.
pause
