@echo off
chcp 65001 >nul
title Установка библиотек

echo Устанавливаю необходимые библиотеки...
echo.

python -m pip install --upgrade pip
python -m pip install Pillow keyboard

echo.
echo Готово! Теперь можно запустить программу:
echo python "image to fix.py"
echo.
pause