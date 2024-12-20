# Обзор библиотеки Libspectrum

!!! abstract "О библиотеке"
    Libspectrum - это Python библиотека для работы со спектрометром через USB интерфейс.
    Предоставляет инструменты для получения, обработки и анализа спектральных данных.

## 📚 API

Полное описание API доступно в [документации API](../reference.md).

## 💻 Поддержка платформ

!!! info "Статус поддержки"
    | ОС | Статус | Реализация USB-слоя |
    |----|--------|---------------------|
    | Windows | ✅ Полная поддержка | Python (ftd2xx) |
    | Linux (Ubuntu) | ✅ Поддержка | C++ (libftdi) |
    | macOS | ❌ Не поддерживается | - |

    Для наилучшей производительности и стабильности рекомендуется использовать **Windows**

!!! warning "Ограничения Linux"
    При работе на Linux возможны ограничения при считывании большого количества кадров:

    - ⚠️ Возможны таймауты при больших объемах данных
    - 📦 Рекомендуется считывать данные батч-пакетами
    - 🔄 Или использовать неблокирующий режим чтения

Подробнее: [Платформенные ограничения](../dev-docs/platform-limitations.md)

## 🚀 Быстрый старт

```python
from pyspectrum import Spectrometer

# Создаем объект спектрометра
spectrometer = Spectrometer()

# Настраиваем параметры
spectrometer.set_config(
    exposure=100,  # время экспозиции в мс
    n_times=10,    # количество снимаемых кадров
    wavelength_calibration_path="calibration.json",  
    dark_signal_path="dark.pkl"  
)

# Измеряем темновой сигнал (с закрытым отверстием)
spectrometer.read_dark_signal()

# Получаем спектр
spectrum = spectrometer.read()

# Работаем с данными
print(f"Размерность данных: {spectrum.shape}")
print(f"Длины волн: {spectrum.wavelength}")
print(f"Интенсивности: {spectrum.intensity}")

# Сохраняем результаты
spectrum.save("measurement.pkl")
```

## 📖 Подробный гайд по использованию

Подробно описываются все `read` методы, предоставляемые библиотекой и приводятся примеры использования.

[📖 Гайд по использованию](guide.md)

## 📊 Работа с данными

### Data

- 📥 Сырые данные с устройства
- 🔢 Базовые математические операции

### Spectrum

- 📈 Обработанные данные
- 📏 Привязка к длинам волн

### Примеры операций

```python
# Вычитание спектров
result = spectrum1 - spectrum2

# Усреднение по времени
average = spectrum[:5] * 0.2  
```

## ⚙️ Конфигурация

| Параметр | Описание | Тип |
|----------|----------|-----|
| `exposure` | Время экспозиции (мс) | int |
| `n_times` | Количество измерений | int |
| `dark_signal_path` | Путь к темновому сигналу | str |
| `wavelength_calibration_path` | Путь к калибровке длин волн | str |

## 🔧 Низкоуровневый доступ

!!! note "UsbDevice"
    При стандартной работе прямое использование UsbDevice не требуется.

    Для низкоуровневого взаимодействия см. [документацию UsbDevice](usb-device.md)
