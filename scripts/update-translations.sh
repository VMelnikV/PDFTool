#!/bin/bash
# Оновлення перекладів (JSON)

echo "🌍 Перевірка перекладів..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

I18N_DIR="src/common/i18n/translations"

# Перевірка наявності файлів
if [ ! -f "$I18N_DIR/uk.json" ]; then
    echo "❌ Помилка: $I18N_DIR/uk.json не знайдено"
    exit 1
fi

if [ ! -f "$I18N_DIR/en.json" ]; then
    echo "❌ Помилка: $I18N_DIR/en.json не знайдено"
    exit 1
fi

# Перевірка валідності JSON
for lang in uk en; do
    if python3 -c "import json; json.load(open('$I18N_DIR/$lang.json'))" 2>/dev/null; then
        echo "✅ $lang.json валідний"
    else
        echo "❌ $lang.json невалідний"
        exit 1
    fi
done

echo "✅ Переклади перевірено!"
