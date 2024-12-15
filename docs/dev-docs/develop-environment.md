# Среда разработки

!!! note "Совместимость"
    ✅ Windows - полная поддержка  
    ✅ Linux (Ubuntu) - поддержка через C++ реализацию  
    ❌ macOS - не поддерживается

## 🚀 Начало работы

### Общие требования

| Компонент | Минимальная версия | Описание |
|-----------|-------------------|-----------|
| Python | 3.11+ | Интерпретатор Python |
| Git | * | Система контроля версий |
| [Hatch](https://hatch.pypa.io/) | * | Система управления проектом |

### Клонирование репозитория

```bash
git clone https://github.com/Routybor/libspectrum.git
cd libspectrum
```

## 🪟 Windows

!!! tip "Простая установка"
    На Windows используется Python-реализация USB-слоя, что упрощает установку и использование.

### Требования

- Python 3.11+
- FTDI D2XX Drivers

### Пошаговая установка

1️⃣ Установите [Python](https://www.python.org/downloads/)  
2️⃣ Установите [FTDI D2XX Drivers](https://ftdichip.com/drivers/d2xx-drivers/)  
3️⃣ Выполните сборку:

```cmd
pip install hatch
hatch build -t wheel
```

## 🐧 Linux (Ubuntu)

!!! warning "C++ реализация"
    На Linux используется C++ реализация USB-слоя для обеспечения совместимости.

### Установка зависимостей

```bash
# Системные зависимости
sudo apt install cmake libftdipp1-dev

# Python зависимости
pip install hatch pybind11
```

### Сборка

```bash
hatch build -t wheel
```

## 🔧 Система сборки

### Используемые инструменты

| Инструмент | Назначение | Конфигурация |
|------------|------------|---------------|
| Hatch | Управление Python проектом | `pyproject.toml` |
| CMake | Сборка C++ компонентов (Linux) | `CMakeLists.txt` |
| PyBind11 | Генерация Python-кода для C++ компонентов (Linux) | `pybind11` |

## 👨‍💻 Разработка

### Работа с документацией

```bash
# Установка зависимостей
pip install -e ".[mkdocs]"

# Запуск локального сервера
mkdocs serve
```

### Тестирование

```bash
pytest /tests
```
