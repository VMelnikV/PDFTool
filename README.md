# 📄 PDF Tool — Універсальний редактор PDF

<div align="center">

![PDF Tool](pdf_icon.png)

**Потужний, безкоштовний та зручний застосунок для роботи з PDF-файлами**

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/VMelnikV/PDFTool/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/VMelnikV/PDFTool/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)](https://appimage.org/)

[![Download Light](https://img.shields.io/badge/download-Light-green.svg)](https://github.com/VMelnikV/PDFTool/releases/latest/download/PDFTool-Light.AppImage)
[![Download Full](https://img.shields.io/badge/download-Full-blue.svg)](https://github.com/VMelnikV/PDFTool/releases/download/PDFTool/PDFTool.AppImage)

</div>

---

## 📖 Про програму

**PDF Tool** — це потужний, безкоштовний та зручний застосунок для роботи з PDF-файлами, створений на Python з використанням PySide6. Програма об'єднує всі необхідні інструменти для щоденної роботи з PDF у єдиному інтерфейсі.

Програма працює як єдиний виконуваний файл (AppImage) і не потребує встановлення додаткових залежностей.

---

## 🚀 Основні можливості

### 🖼️ Конвертація зображень у PDF
- Підтримка форматів: PNG, JPG, JPEG, BMP, TIFF
- Конвертація одного або кількох зображень в єдиний PDF
- Автоматичне іменування на основі назви першого зображення
- Drag & Drop підтримка

### 📄 Об'єднання PDF
- Склеювання кількох PDF-файлів в один
- Можливість зміни порядку сторінок
- Автоматичне іменування результату

### ✂️ Розділення PDF
- Розділення на окремі сторінки
- Виділення діапазону сторінок
- Виділення однієї сторінки
- Збереження в окрему папку

### ✍️ Заповнення форм
- Автоматичне виявлення полів форми
- Підтримка текстових полів, чекбоксів та списків
- Збереження заповненої форми

### 📦 Стиснення PDF
- Три рівні стиснення: Екран (72 DPI), Електронна книга (150 DPI), Друк (300 DPI)
- Налаштування якості JPEG (1-100)
- Відображення відсотка зменшення розміру
- Використання Ghostscript для максимальної ефективності

---

## 🎯 Ключові особливості

- **Drag & Drop** — просто перетягніть файли у вікно програми
- **Автоматичне іменування** — програма сама пропонує назву файлу
- **Перевірка на існування** — при створенні файлу, який вже існує, програма запропонує перезаписати, змінити назву або скасувати
- **Прогрес-бар** — візуальний індикатор виконання операцій
- **Статусна стрічка** — інформація про поточний стан програми
- **Портативність** — працює як єдиний виконуваний файл (AppImage)

---

## 🛠️ Технології

| Компонент | Опис |
|-----------|------|
| **Python 3.12** | Мова програмування |
| **PySide6** | Графічний інтерфейс (Qt для Python) |
| **Pillow** | Робота із зображеннями |
| **pypdf** | Маніпуляції з PDF (об'єднання, розділення) |
| **PyPDFForm** | Заповнення PDF-форм |
| **Ghostscript** | Стиснення PDF |

---

## 💻 Системні вимоги

- **Linux** (Ubuntu 20.04 або новіший, або будь-який дистрибутив з підтримкою AppImage)
- **Мінімум 500 MB** вільного місця на диску
- **Мінімум 2 GB** оперативної пам'яті

---

## 📦 Встановлення та запуск

У вас є вибір між двома версіями:

### 🪶 PDFTool-Light.AppImage (рекомендована)

**Розмір:** ~3 МБ  
**Вимоги:** Потребує попередньо встановлених системних бібліотек.

```bash
# Завантажте легку версію
wget https://github.com/VMelnikV/PDFTool/releases/latest/download/PDFTool-Light.AppImage

# Зробіть виконуваним
chmod +x PDFTool-Light.AppImage

# Запустіть
./PDFTool-Light.AppImage
```

**Встановлення залежностей (Ubuntu/Debian):**
```bash
sudo apt install python3 python3-pip python3-pyside6 python3-pil python3-pypdf ghostscript
pip install PyPDFForm
```

### 📦 PDFTool-x86_64.AppImage (повна версія)

**Розмір:** ~285 МБ  
**Вимоги:** Не потребує встановлення додаткових бібліотек. Працює "з коробки".

```bash
# Завантажте повну версію
wget https://github.com/VMelnikV/PDFTool/releases/download/PDFTool/PDFTool.AppImage

# Зробіть виконуваним
chmod +x PDFTool.AppImage

# Запустіть
./PDFTool.AppImage
```

### З вихідного коду

```bash
# Клонуйте репозиторій
git clone https://github.com/VMelnikV/PDFTool.git
cd PDFTool

# Встановіть залежності
pip install -r requirements.txt

# Запустіть програму
python3 cod/main.py
```
## 🙏 Подяки

DeepSeek — за те, що жодного разу не сказав "це неможливо" 😉

PySide6 — за потужний GUI-фреймворк

Ghostscript — за ефективне стиснення PDF

AppImage — за можливість створювати портативні застосунки

Pillow — за роботу із зображеннями

pypdf — за маніпуляції з PDF

PyPDFForm — за заповнення форм

Copilot - за допомогу з зображенням

<div align="center">

Зроблено з ❤️ для спільноти

</div>


<div align="center">

## Якщо є бажання віддячити та підтримати мене

![https://send.monobank.ua/5M8pMbQG3A](https://github.com/VMelnikV/PDFTool/blob/main/mono.png)

https://send.monobank.ua/5M8pMbQG3A


</div>

