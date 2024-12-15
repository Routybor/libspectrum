# Libspectrum

<div align="center">

![PyPI Version](https://img.shields.io/pypi/v/libspectrum)
![Build Status](https://img.shields.io/github/actions/workflow/status/routybor/libspectrum/release.yml)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://routybor.github.io/libspectrum/)

Python библиотека для работы со спектрометрами производства VMK через USB интерфейс.

🔍 [Документация](https://routybor.github.io/libspectrum/)
📦 [PyPI](https://pypi.org/project/libspectrum/)

</div>

## ✨ Возможности

- 📈 Получение спектральных данных
- 🎯 Калибровка по темновому сигналу
- ⚙️ Возможность неблокирующего и непрерывного чтения
- 💾 Сохранение и загрузка измерений
- ➗ Математические операции со спектрами

## 📈 Демо приложение

В рамках проекта для демонстрации возможностей неблокирующего чтения было написанно небольшое
демо приложение, для визуализации спектра в реальном времени.

<video width="640" height="360" controls>
  <source src="docs/gui_short.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## 💻 Поддерживаемые платформы

| ОС | Статус | Реализация |
|----|--------|------------|
| Windows | ✅ | Python + ftd2xx |
| Linux (Ubuntu) | ⚠️ | C++ + libftdi |
| macOS | ❌ | Не поддерживается |
