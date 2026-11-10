@echo off
rem Запуск портала клуба выпускников на компьютере с Windows.
rem Нужен установленный Python 3.12 и доступ в интернет при первом запуске.
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python не найден. Установите Python 3.12 с сайта python.org
    echo и при установке отметьте пункт "Add python.exe to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Создаю виртуальное окружение...
    python -m venv .venv
    if errorlevel 1 goto failed
)

echo Устанавливаю библиотеки...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto failed

echo Готовлю базу данных...
".venv\Scripts\python.exe" manage.py migrate --no-input
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -X utf8 manage.py seed_demo

echo.
echo Портал запущен: http://127.0.0.1:8000
echo Логины и пароли демонстрационных ролей указаны в файле README.md
echo Чтобы остановить портал, закройте это окно.
echo.
start "" http://127.0.0.1:8000
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
goto :eof

:failed
echo.
echo Не удалось подготовить портал. Проверьте подключение к интернету и версию Python.
pause
exit /b 1
