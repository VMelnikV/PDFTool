#!/bin/bash
# Збірка AppImage для PDF Tool

set -e

# Версія: спершу зі змінної середовища, потім з git describe, потім fallback
if [ -n "$VERSION" ]; then
    VERSION="${VERSION#v}"
else
    VERSION="$(git describe --tags --always --dirty 2>/dev/null | sed 's/^v//')"
fi
VERSION="${VERSION:-1.0.0}"

echo "🪶 Збірка AppImage (версія: $VERSION)..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Пошук appimagetool — спершу розпакований, потім як AppImage, потім системний
APPIMAGETOOL=""
for path in \
    "$PROJECT_ROOT/appimagetool" \
    "$PROJECT_ROOT/appimagetool-extracted/AppRun" \
    "$PROJECT_ROOT/appimagetool-x86_64.AppImage" \
    "$HOME/pdf/appimagetool-x86_64.AppImage" \
    "/usr/local/bin/appimagetool"
do
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

APPIMAGE_VERSIONED="packages/appimage/PDFTool-${VERSION}.AppImage"
APPIMAGE_STABLE="packages/appimage/PDFTool-x86_64.AppImage"

ARCH=x86_64 "$APPIMAGETOOL" \
    "packaging/appimage/app/AppDir" \
    "$APPIMAGE_VERSIONED"

# Копія зі стабільною назвою — для URL "latest/download/PDFTool-x86_64.AppImage"
cp "$APPIMAGE_VERSIONED" "$APPIMAGE_STABLE"

echo "✅ AppImage створено:"
echo "   - $APPIMAGE_VERSIONED"
echo "   - $APPIMAGE_STABLE"
