# Установка библиотеки

!!! note "Требования"
    - Python 3.11 или выше
    - Драйвер D2XX для Windows
    - Драйвер libftdi для Linux (на большинстве современных дистрибутивов предустановлен)

## 🐧 Linux

!!! info "Тестировалось на Ubuntu 22.04 LTS"

### 1️⃣ Установка Python и pip

```bash
sudo apt install python3 python3-pip
```

### 2️⃣ Установка библиотеки

```bash
pip install libspectrum
```

### 3️⃣ Настройка прав доступа к USB

!!! warning "Важно"
    Этот шаг необходим для работы с устройством без прав root

```bash
echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014",  MODE="0666"' | sudo tee /etc/udev/rules.d/69-spectrometer.rules
sudo udevadm control --reload
```

## 🪟 Windows

### 1️⃣ Установка драйверов FTDI

!!! tip "Примечание"
    Если на компьютере ранее работал `Atom`, этот шаг можно пропустить

- Скачайте [драйвер FTDI](https://ftdichip.com/drivers/d2xx-drivers/)
- Доступен portable установщик: [CDM212364_Setup.zip](https://ftdichip.com/wp-content/uploads/2021/08/CDM212364_Setup.zip)

!!! tip
    [Официальный гайд FTDI по установке драйверов](https://ftdichip.com/document/installation-guides/)

### 2️⃣ Установка зависимостей

- Установите [Распространяемый пакет Visual C++ для Visual Studio 2015](https://www.microsoft.com/ru-RU/download/details.aspx?id=48145)
- Установите **64-битный** Python (3.11+)

### 3️⃣ Установка библиотеки

```cmd
pip install libspectrum
```

## 🔍 Проверка установки

Для проверки корректности установки выполните в Python:

```python
from pyspectrum import Spectrometer

# Должно выполниться без ошибок
spectrometer = Spectrometer()
```

!!! success "Готово!"
    После успешного выполнения всех шагов библиотека готова к использованию

## 🚨 Возможные проблемы

| Проблема | Решение |
|----------|---------|
| Ошибка доступа к USB (Linux) | Проверьте правила udev и перезагрузите систему |
| ImportError (Windows) | Убедитесь, что установлен правильный драйвер FTDI |
| ModuleNotFoundError | Проверьте версию Python и правильность установки библиотеки |

!!! tip "Поддержка"
    При возникновении проблем создайте issue на GitHub.
