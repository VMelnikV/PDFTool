#!/usr/bin/env python3
"""
PDF Tool Launcher
Перевіряє наявність системних бібліотек та запускає програму
"""

import sys
import subprocess
import importlib.util
import os
from typing import Dict, List, Tuple

# Список необхідних бібліотек
REQUIREMENTS = {
    "PySide6": {
        "pip": "PySide6",
        "apt": "python3-pyside6",
        "import_name": "PySide6",
        "check_cmd": "python3 -c 'import PySide6'"
    },
    "Pillow": {
        "pip": "Pillow",
        "apt": "python3-pil",
        "import_name": "PIL",
        "check_cmd": "python3 -c 'import PIL'"
    },
    "pypdf": {
        "pip": "pypdf",
        "apt": "python3-pypdf",
        "import_name": "pypdf",
        "check_cmd": "python3 -c 'import pypdf'"
    },
    "PyPDFForm": {
        "pip": "PyPDFForm",
        "apt": "",  # Немає в репозиторіях
        "import_name": "PyPDFForm",
        "check_cmd": "python3 -c 'import PyPDFForm'"
    },
    "Ghostscript": {
        "pip": "",
        "apt": "ghostscript",
        "import_name": None,
        "is_binary": True,
        "binary": "gs",
        "check_cmd": "which gs"
    }
}

class DependencyChecker:
    """Перевіряє наявність залежностей в системі"""
    
    def __init__(self):
        self.missing = []
        self.installed = []
    
    def check_python_module(self, module_name: str) -> bool:
        """Перевіряє чи встановлений Python-модуль в системі"""
        try:
            # Перевіряємо через importlib
            if importlib.util.find_spec(module_name) is not None:
                return True
            return False
        except (ImportError, AttributeError):
            return False
    
    def check_system_binary(self, binary_name: str) -> bool:
        """Перевіряє чи існує системна утиліта"""
        try:
            result = subprocess.run(
                ['which', binary_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except:
            return False
    
    def check_all(self) -> Tuple[List[str], List[str]]:
        """Перевіряє всі залежності"""
        print("\n🔍 Перевірка системних залежностей...")
        print("-" * 50)
        
        for name, info in REQUIREMENTS.items():
            is_installed = False
            
            if info.get("is_binary", False):
                is_installed = self.check_system_binary(info["binary"])
            else:
                is_installed = self.check_python_module(info["import_name"])
            
            if is_installed:
                self.installed.append(name)
                print(f"  ✅ {name} - знайдено")
            else:
                self.missing.append(name)
                print(f"  ❌ {name} - НЕ ЗНАЙДЕНО")
        
        print("-" * 50)
        print(f"✅ Встановлено: {len(self.installed)} з {len(REQUIREMENTS)}")
        
        return self.installed, self.missing
    
    def show_install_instructions(self):
        """Показує інструкції для встановлення відсутніх бібліотек"""
        if not self.missing:
            return
        
        print("\n" + "=" * 60)
        print("⚠️  ВІДСУТНІ ЗАЛЕЖНОСТІ В СИСТЕМІ")
        print("=" * 60)
        
        print("\nНе знайдено наступних бібліотек:")
        for name in self.missing:
            print(f"  ❌ {name}")
        
        print("\n" + "-" * 60)
        print("📦 ЯК ВСТАНОВИТИ")
        print("-" * 60)
        
        # Групуємо команди
        apt_packages = []
        pip_packages = []
        manual = []
        
        for name in self.missing:
            info = REQUIREMENTS[name]
            if info.get("apt"):
                apt_packages.append(info["apt"])
            elif info.get("pip"):
                pip_packages.append(info["pip"])
            else:
                manual.append(name)
        
        if apt_packages:
            print("\n📌 Через систему пакування (apt):")
            print(f"  sudo apt install {' '.join(apt_packages)}")
        
        if pip_packages:
            print("\n📌 Через pip:")
            for pkg in pip_packages:
                print(f"  pip install {pkg}")
        
        if manual:
            print("\n📌 Вручну:")
            for name in manual:
                print(f"  {name}")
        
        print("\n" + "=" * 60)
        print("💡 Після встановлення всіх залежностей запустіть програму знову.")
        print("=" * 60 + "\n")
        
        # Пропонуємо автоматичне встановлення
        if apt_packages or pip_packages:
            print("\n❓ Бажаєте спробувати встановити залежності автоматично?")
            print("   (потрібні права sudo для apt)")
            response = input("   Введіть 'y' або 'n': ").strip().lower()
            if response == 'y':
                self.auto_install(apt_packages, pip_packages)
    
    def auto_install(self, apt_packages, pip_packages):
        """Автоматично встановлює відсутні залежності"""
        print("\n🔧 Встановлення залежностей...")
        
        if apt_packages:
            print(f"📦 Встановлення через apt: {' '.join(apt_packages)}")
            try:
                subprocess.run(
                    ['sudo', 'apt', 'install', '-y'] + apt_packages,
                    check=True
                )
                print("✅ apt пакети встановлено")
            except subprocess.CalledProcessError:
                print("❌ Помилка встановлення apt пакетів")
        
        if pip_packages:
            print(f"📦 Встановлення через pip: {' '.join(pip_packages)}")
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install'] + pip_packages,
                    check=True
                )
                print("✅ pip пакети встановлено")
            except subprocess.CalledProcessError:
                print("❌ Помилка встановлення pip пакетів")

def main():
    """Головна функція"""
    # Перевіряємо аргументи
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print("""
PDF Tool Launcher

Перевіряє наявність системних бібліотек та запускає програму.

Використання:
    python3 launcher.py [OPTIONS]

Опції:
    --help, -h         Показати цю довідку
    --check-only       Тільки перевірити залежності, не запускати програму
    --install          Показати команди встановлення та спробувати встановити
    --force            Примусово запустити програму без перевірки

Приклад:
    python3 launcher.py          # Перевірити та запустити
    python3 launcher.py --check-only   # Тільки перевірити
    python3 launcher.py --install      # Встановити залежності
""")
        return 0
    
    checker = DependencyChecker()
    installed, missing = checker.check_all()
    
    if "--install" in args and missing:
        checker.show_install_instructions()
        # Після встановлення перевіряємо знову
        installed, missing = checker.check_all()
        if not missing:
            print("\n✅ Всі залежності встановлено!")
    
    if "--check-only" in args:
        if missing:
            print("\n⚠️  Деякі залежності відсутні.")
            checker.show_install_instructions()
        else:
            print("\n✅ Всі залежності встановлені!")
        return 1 if missing else 0
    
    if missing and "--force" not in args:
        checker.show_install_instructions()
        return 1
    
    if "--force" in args and missing:
        print("\n⚠️  Примусовий запуск (деякі функції можуть не працювати)")
    
    # Запускаємо основну програму
    print("\n🚀 Запуск PDF Tool...")
    print("-" * 50 + "\n")
    
    try:
        # Імпортуємо та запускаємо main.py
        import main
        main.main()
    except ImportError as e:
        print(f"❌ Помилка імпорту: {e}")
        print("Переконайтеся, що файл main.py знаходиться в тій же папці.")
        return 1
    except Exception as e:
        print(f"❌ Помилка запуску: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
