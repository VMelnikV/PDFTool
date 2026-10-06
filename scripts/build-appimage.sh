#!/bin/bash
# Збірка AppImage для PDF Tool

set -e

VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "1.0.0")

echo "🪶 Збірка AppImage..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Пошук appimagetool
APPIMAGETOOL=""
for path in "$PROJECT_ROOT/appimagetool-x86_64.AppImage" "$HOME/pdf/appimagetool-x86_64.AppImage" "/usr/local/bin/appimagetool"; do
    if [ -f "$path" ]; then
        APPIMAGETOOL="$path"
        break
    fi
done

if [ -z "$APPIMAGETOOL" ]; then
    echo "❌ Помилка: appimagetool не знайдено"
    exit 1
fi

echo "📦 Використовуємо appimagetool: $APPIMAGETOOL"

# 1. Збірка ELF через PyInstaller
echo "📦 Збірка ELF через PyInstaller..."
cd "src/app"
rm -rf dist build

pyinstaller --name "PDFTool" \
    --windowed \
    --onefile \
    --add-data "tabs:tabs" \
    --add-data "utils:utils" \
    --add-data "pdf_tool.py:." \
    --add-data "launcher.py:." \
    --add-data "../common:common" \
    --add-data "../common/resources/icons/pdf_icon.png:." \
    --hidden-import PySide6 \
    --hidden-import PIL \
    --hidden-import pypdf \
    --hidden-import PyPDFForm \
    main.py

cd "$PROJECT_ROOT"

# 2. Збірка AppImage через appimage-builder
echo "📦 Збірка AppImage через appimage-builder..."
cd "packaging/appimage/app"
rm -rf AppDir
appimage-builder --recipe AppImageBuilder.yml --skip-tests
cd "$PROJECT_ROOT"

# 3. Створення фінального AppImage
echo "📦 Створення AppImage..."
mkdir -p packages/appimage
ARCH=x86_64 "$APPIMAGETOOL" \
    "packaging/appimage/app/AppDir" \
    "packages/appimage/PDFTool-${VERSION}.AppImage"

echo "✅ AppImage створено: packages/appimage/PDFTool-${VERSION}.AppImage"
