#!/bin/bash
# Збірка AppImage для Full або Light версії

set -e

VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "1.0.0")
TYPE=${1:-full}  # full або light

echo "🪶 Збірка AppImage ($TYPE версія)..."

# Перевірка
if [ "$TYPE" != "full" ] && [ "$TYPE" != "light" ]; then
    echo "❌ Помилка: вкажіть 'full' або 'light'"
    exit 1
fi

# Шляхи
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 1. Збірка ELF через PyInstaller
echo "📦 Збірка ELF через PyInstaller..."
cd "src/$TYPE"
rm -rf dist build

if [ "$TYPE" = "full" ]; then
    pyinstaller --name "PDFTool" \
        --windowed \
        --onefile \
        --add-data "tabs:tabs" \
        --add-data "utils:utils" \
        --add-data "pdf_tool.py:." \
        --add-data "../common:common" \
        --add-data "../common/resources/icons/pdf_icon.png:." \
        --add-data "ghostscript:ghostscript" \
        --hidden-import PySide6 \
        --hidden-import PIL \
        --hidden-import pypdf \
        --hidden-import PyPDFForm \
        main.py
else
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
fi

cd "$PROJECT_ROOT"

# 2. Збірка AppImage через appimage-builder
echo "📦 Збірка AppImage через appimage-builder..."
cd "packaging/appimage/$TYPE"
rm -rf AppDir
appimage-builder --recipe AppImageBuilder.yml --skip-tests
cd "$PROJECT_ROOT"

# 3. Створення фінального AppImage
echo "📦 Створення AppImage..."
mkdir -p packages/appimage
ARCH=x86_64 "$HOME/pdf/appimagetool-x86_64.AppImage" \
    "packaging/appimage/$TYPE/AppDir" \
    "packages/appimage/PDFTool-${TYPE^}-${VERSION}.AppImage"

echo "✅ AppImage ($TYPE) створено: packages/appimage/PDFTool-${TYPE^}-${VERSION}.AppImage"