#!/bin/bash
# apprun.sh - обгортка для запуску PDF Tool

# Отримуємо шлях до папки, де знаходиться скрипт
SCRIPT_DIR=$(dirname "$0")

# Знаходимо Python
PYTHON_CMD=$(which python3 || which python)

if [ -z "$PYTHON_CMD" ]; then
    echo "Помилка: Python не знайдено в системі"
    echo "Будь ласка, встановіть Python 3.12 або новіший"
    exit 1
fi

# Запускаємо launcher.py з тієї ж папки
exec "$PYTHON_CMD" "$SCRIPT_DIR/launcher.py" "$@"
