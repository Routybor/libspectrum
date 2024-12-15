---
hide:
- toc
---

# Архитектурный обзор

!!! abstract "Общая структура"
    Библиотека разделена на два основных компонента:

    **Core Python Library**
    : Основная функциональность спектрометра (обработка данных и высокоуровневое управление)
    
    **USB Communication Layer**
    : Слой коммуникации с USB-устройством (реализации на Python и C++)

## 🏗️ Компонентная архитектура

```mermaid
graph TB
    subgraph Core["Core Python Library"]
        A[spectrometer.py<br/>Spectrometer]
        B[data.py<br/>Data, Spectrum]
        A -->|uses| B
    end

    subgraph Python["USB Communication Layer (Python)"]
        C[usb_device.py<br/>UsbDevice]
        D[usb_context.py<br/>UsbContext]
        C -->|uses| D
    end

    subgraph Cpp["USB Communication Layer (C++)"]
        E[UsbDevice.cpp<br/>UsbDevice]
        F[UsbContext.cpp<br/>UsbContext]
        G[Frame.cpp<br/>Frame]
        E -->|uses| F
        E -->|uses| G
    end

    Core -->|depends on| Python
    Core -.->|depends on| Cpp

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#fdb,stroke:#333,stroke-width:2px
    style D fill:#fdb,stroke:#333,stroke-width:2px
    style E fill:#dfd,stroke:#333,stroke-width:2px
    style F fill:#dfd,stroke:#333,stroke-width:2px
    style G fill:#dfd,stroke:#333,stroke-width:2px
```

!!! info "Платформенная специфика"
    - 🪟 **Windows**: Использует Python-реализацию USB-слоя
    - 🐧 **Linux**: Использует C++-реализацию USB-слоя
    - 🍎 **macOS**: Не поддерживается

## 📦 Компоненты библиотеки

### Core Python Library

#### 🌈 Spectrometer (spectrometer.py)

- Высокоуровневый интерфейс управления
- Конфигурация и калибровка
- Координация сбора данных
- Абстракция над USB-слоем

#### 📊 Data & Spectrum (data.py)

- Структуры данных измерений
- Математические операции
- Персистентность данных

### USB Communication Layer (Python)

#### 🔌 UsbDevice (usb_device.py)

- Реализация протокола устройства
- Управление конфигурацией
- Обработка кадров данных

#### 🛠️ UsbContext (usb_context.py)

- Низкоуровневые USB операции
- Управление подключением
- Работа с ftd2xx

### USB Communication Layer (C++)

#### 🔌 UsbDevice (UsbDevice.cpp)

- C++ реализация протокола
- Управление устройством
- Интеграция через pybind11

#### 🛠️ UsbContext (UsbContext.cpp)

- Нативные USB операции
- Работа с libftdi

#### 📥 Frame (Frame.cpp)

- Структура кадра данных
- Конвертация в numpy

## 🔄 Поток данных

```mermaid
sequenceDiagram
    participant App as User Application
    participant Spec as Spectrometer.py
    participant USB as USB Layer<br/>(Python or C++)
    participant Dev as Physical Device

    Note over USB: Единый интерфейс для обеих реализаций
    
    App->>Spec: read()
    activate Spec
    
    Spec->>USB: set_timer(exposure_ms)
    USB->>Dev: COMMAND_WRITE_TIMER
    Dev-->>USB: reply OK
    
    Spec->>USB: read_frame(n_times)
    activate USB
    
    USB->>Dev: COMMAND_READ_FRAME
    Dev-->>USB: #DAT packets
    
    Note over USB: Обработка сырых данных
    
    USB-->>Spec: Frame(samples, clipped)
    deactivate USB
    
    Note over Spec: Коррекция темнового сигнала
    
    Spec-->>App: Spectrum object
    deactivate Spec
```

!!! tip "Ключевые особенности"
    - 🔄 Единый интерфейс для обеих реализаций USB-слоя
    - 🔒 Изоляция платформо-зависимого кода
    - 📊 Унифицированная обработка данных
