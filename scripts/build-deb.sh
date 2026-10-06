#!/bin/bash
# Збірка DEB пакета для PDF Tool

set -e

# Версія без префіксу "v" (для Debian)
VERSION=$(git describe --tags --always --dirty 2>/dev/null | sed 's/^v//' || echo "1.0.0")

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📦 Збірка DEB пакета (версія: $VERSION)..."

# Створення тимчасової папки
BUILD_DIR="build/deb"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Копіюємо файли
cp -r src "$BUILD_DIR/"
cp -r packaging/debian/app "$BUILD_DIR/debian"

# Додаємо версію в changelog
sed -i "s/1.0.0/$VERSION/g" "$BUILD_DIR/debian/changelog"

# Збірка
cd "$BUILD_DIR"
dpkg-buildpackage -us -uc -b

cd "$PROJECT_ROOT"
mkdir -p packages/deb
mv build/*.deb packages/deb/ 2>/dev/null || true

echo "✅ DEB пакет створено!"
ls -la packages/deb/
