# Libspectrum

<div align="center">

<!-- ![PyPI Version](https://img.shields.io/pypi/v/vmk-spectrum) -->
![Build Status](https://img.shields.io/github/actions/workflow/status/routybor/libspectrum/release.yml)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://routybor.github.io/libspectrum/)

Python библиотека для работы со спектрометрами производства VMK через USB интерфейс.

🔍 [Документация](https://routybor.github.io/libspectrum/)
<!-- 📦 [PyPI](https://pypi.org/project/vmk-spectrum/) | -->

</div>

## ✨ Возможности

- 📈 Получение спектральных данных
- 🎯 Калибровка по темновому сигналу
- 📏 Калибровка по длинам волн
- 💾 Сохранение и загрузка измерений
- ➗ Математические операции со спектрами

## 💻 Поддерживаемые платформы

| ОС | Статус | Реализация |
|----|--------|------------|
| Windows | ✅ | Python + ftd2xx |
| Linux (Ubuntu) | ⚠️ | C++ + libftdi |
| macOS | ❌ | Не поддерживается |
