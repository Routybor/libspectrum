---
hide:
- toc
- navigation
---

# Libspectrum

!!! abstract ""
    Python библиотека для работы со спектрометром через USB интерфейс

## 🔍 API Reference

[Полная документация API →](reference.md)

## 📖 Руководства

!!! example "Для пользователя"
    - 📘 [Обзор библиотеки](user-docs/overview.md)
    - 📖 [Гайд по использованию](user-docs/guide.md)
    - 💿 [Установка](user-docs/installation.md)
    - 🔌 [Работа с UsbDevice](user-docs/usb-device.md)

!!! example "Для разработчика"
    - 🏗️ [Архитектурный обзор](dev-docs/architecture.md)
    - ⚙️ [Среда разработки](dev-docs/develop-environment.md)
    - 💻 [Платформенные ограничения](dev-docs/platform-limitations.md)
    - 🔧 [UsbDevice](dev-docs/usb-device.md)
    - 🛠️ [UsbContext](dev-docs/usb-context.md)
    - 📚 [Документация драйверов](dev-docs/driver-docs.md)
    - 📖 [Документация команд устройства](dev-docs/cmd.md)

## 📊 Примеры использования

!!! tip "Базовые примеры"
    - 📈 [Запись спектра](examples/record_spectrum.ipynb)
    : Базовый пример получения и сохранения данных

!!! tip "Практические применения"
    - 📈 [Визуализация спектра в реальном времени](examples/real_time_demo.py)
    : Визуализация получаемых данных в реальном времени

    - 🌡️ [Пирометр](examples/pyrometer.ipynb)
    : Измерение температуры по спектру излучения

    - 💡 [Характеристики ламп](examples/led_parameters.ipynb)
    : Анализ спектральных характеристик источников света
    
    - 🎨 [Колориметр](examples/colorimeter.ipynb)
    : Измерение цветовых характеристик

## 📈 Пример визуализации спектра в реальном времени

<video width="640" height="360" controls>
  <source src="gui_short.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## 💻 Поддерживаемые платформы

| ОС | Статус | Описание |
|----|--------|----------|
| Windows | ✅ | Полная поддержка |
| Linux | ⚠️ | Ограниченная поддержка |
| MacOS | ❌ | Не поддерживается |

!!! info "Подробнее"
    Детальная информация о поддержке платформ доступна в разделе [Платформенные ограничения](dev-docs/platform-limitations.md)
