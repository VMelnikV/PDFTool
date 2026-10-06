#!/usr/bin/env python3
"""
PDF Tool Launcher (Light version)
Перевіряє наявність системних бібліотек та запускає програму
"""

import sys
import subprocess
import importlib.util
import os
from typing import Dict, List, Tuple

# ==================================================
# НАЛАШТУВАННЯ ШЛЯХІВ
# ==================================================

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)

# Додаємо шлях до src для common
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Додаємо поточну папку для main.py та pdf_tool.py
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ==================================================
# ІМПОРТ ПЕРЕКЛАДІВ
# ==================================================

try:
    from common.i18n.translator import translator
except ImportError:
    class FallbackTranslator:
        def tr(self, key, context='common'):
            return key
    translator = FallbackTranslator()

# ==================================================
# СПИСОК НЕОБХІДНИХ БІБЛІОТЕК
# ==================================================

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
        print(f"\n{translator.tr('launcher_checking', 'launcher')}")
        print("-" * 50)
        
        for name, info in REQUIREMENTS.items():
            is_installed = False
            
            if info.get("is_binary", False):
                is_installed = self.check_system_binary(info["binary"])
            else:
                is_installed = self.check_python_module(info["import_name"])
            
            if is_installed:
                self.installed.append(name)
                print(f"  ✅ {name} - {translator.tr('launcher_found', 'launcher')}")
            else:
                self.missing.append(name)
                print(f"  ❌ {name} - {translator.tr('launcher_not_found', 'launcher')}")
        
        print("-" * 50)
        print(f"✅ {translator.tr('launcher_installed', 'launcher').format(count=len(self.installed), total=len(REQUIREMENTS))}")
        
        return self.installed, self.missing
    
    def show_install_instructions(self):
        """Показує інструкції для встановлення відсутніх бібліотек"""
        if not self.missing:
            return
        
        print("\n" + "=" * 60)
        print(f"⚠️  {translator.tr('launcher_missing_header', 'launcher')}")
        print("=" * 60)
        
        print(f"\n{translator.tr('launcher_missing_list', 'launcher')}")
        for name in self.missing:
            print(f"  ❌ {name}")
        
        print("\n" + "-" * 60)
        print(f"📦 {translator.tr('launcher_how_to_install', 'launcher')}")
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
            print(f"\n📌 {translator.tr('launcher_through_apt', 'launcher')}")
            print(f"  sudo apt install {' '.join(apt_packages)}")
        
        if pip_packages:
            print(f"\n📌 {translator.tr('launcher_through_pip', 'launcher')}")
            for pkg in pip_packages:
                print(f"  pip install {pkg}")
        
        if manual:
            print(f"\n📌 {translator.tr('launcher_manual', 'launcher')}")
            for name in manual:
                print(f"  {name}")
        
        print("\n" + "=" * 60)
        print(f"💡 {translator.tr('launcher_after_install', 'launcher')}")
        print("=" * 60 + "\n")
        
        # Пропонуємо автоматичне встановлення
        if apt_packages or pip_packages:
            print(f"\n❓ {translator.tr('launcher_auto_install_question', 'launcher')}")
            print(f"   {translator.tr('launcher_sudo_note', 'launcher')}")
            response = input(f"   {translator.tr('launcher_enter_y_or_n', 'launcher')} ").strip().lower()
            if response == 'y':
                self.auto_install(apt_packages, pip_packages)
    
    def auto_install(self, apt_packages, pip_packages):
        """Автоматично встановлює відсутні залежності"""
        print(f"\n🔧 {translator.tr('launcher_installing', 'launcher')}")
        
        if apt_packages:
            print(f"📦 {translator.tr('launcher_installing_apt', 'launcher').format(packages=' '.join(apt_packages))}")
            try:
                subprocess.run(
                    ['sudo', 'apt', 'install', '-y'] + apt_packages,
                    check=True
                )
                print(f"✅ {translator.tr('launcher_apt_done', 'launcher')}")
            except subprocess.CalledProcessError:
                print(f"❌ {translator.tr('launcher_apt_error', 'launcher')}")
        
        if pip_packages:
            print(f"📦 {translator.tr('launcher_installing_pip', 'launcher').format(packages=' '.join(pip_packages))}")
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install'] + pip_packages,
                    check=True
                )
                print(f"✅ {translator.tr('launcher_pip_done', 'launcher')}")
            except subprocess.CalledProcessError:
                print(f"❌ {translator.tr('launcher_pip_error', 'launcher')}")


def print_help():
    """Показує довідку"""
    print(f"""
{translator.tr('launcher_help_title', 'launcher')}

{translator.tr('launcher_help_description', 'launcher')}

{translator.tr('launcher_help_usage', 'launcher')}
    python3 launcher.py [OPTIONS]

{translator.tr('launcher_help_options', 'launcher')}
    --help, -h         {translator.tr('launcher_help_help', 'launcher')}
    --check-only       {translator.tr('launcher_help_check_only', 'launcher')}
    --install          {translator.tr('launcher_help_install', 'launcher')}
    --force            {translator.tr('launcher_help_force', 'launcher')}

{translator.tr('launcher_help_example', 'launcher')}
    python3 launcher.py          {translator.tr('launcher_help_example_check', 'launcher')}
    python3 launcher.py --check-only   {translator.tr('launcher_help_example_check_only', 'launcher')}
    python3 launcher.py --install      {translator.tr('launcher_help_example_install', 'launcher')}
""")


def main():
    """Головна функція"""
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print_help()
        return 0
    
    checker = DependencyChecker()
    installed, missing = checker.check_all()
    
    if "--install" in args and missing:
        checker.show_install_instructions()
        installed, missing = checker.check_all()
        if not missing:
            print(f"\n✅ {translator.tr('launcher_all_installed', 'launcher')}")
    
    if "--check-only" in args:
        if missing:
            print(f"\n⚠️  {translator.tr('launcher_some_missing', 'launcher')}")
            checker.show_install_instructions()
        else:
            print(f"\n✅ {translator.tr('launcher_all_installed', 'launcher')}")
        return 1 if missing else 0
    
    if missing and "--force" not in args:
        checker.show_install_instructions()
        return 1
    
    if "--force" in args and missing:
        print(f"\n⚠️  {translator.tr('launcher_force_warning', 'launcher')}")
    
    print(f"\n🚀 {translator.tr('launcher_starting', 'launcher')}")
    print("-" * 50 + "\n")
    
    try:
        # Імпортуємо main.py з поточної папки
        import main
        main.main()
    except ImportError as e:
        print(f"❌ {translator.tr('launcher_import_error', 'launcher')}: {e}")
        print(translator.tr('launcher_check_main', 'launcher'))
        return 1
    except Exception as e:
        print(f"❌ {translator.tr('launcher_run_error', 'launcher')}: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
