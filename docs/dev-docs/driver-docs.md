# Документация драйверов

В этом разделе описаны различные драйверы и библиотеки для работы с FTDI устройствами, а также их документация.

## D2XX драйвер

!!! info "Официальная документация"
    Подробное руководство по работе с `D2XX` драйвером доступно в [D2XX Programmer Guide](https://ftdichip.com/wp-content/uploads/2023/09/D2XX_Programmers_Guide.pdf)

В данном проекте используется Python wrapper библиотека [ftd2xx](https://github.com/ftd2xx/ftd2xx) версии 1.3.8.

[📚 Документация ftd2xx](https://ftd2xx.github.io/ftd2xx/)

## Libftdi драйвер

[📚 API документация Libftdi](https://www.intra2net.com/en/developer/libftdi/documentation/)

## Альтернативные библиотеки

### pylibftdi

[pylibftdi](https://github.com/codedstructure/pylibftdi) - это Python wrapper для работы с `Libftdi`.

!!! warning "Известные проблемы"
    При тестировании библиотеки были обнаружены технические трудности:

    - Случайные timeout'ы при операциях чтения
    - Нестабильная работа при длительном использовании

### pyftdi

[pyftdi](https://github.com/eblot/pyftdi) - это независимая Python библиотека, которая:

- Не использует драйверы FTDI
- Работает напрямую через libusb
- Официально поддерживает Unix системы

!!! warning "Ограничения"
    При тестировании обнаружены проблемы, аналогичные `pylibftdi`

## Планы развития

!!! tip "Future Goals"
    - Детальное исследование работы `pyftdi`
    - Поиск решений для обнаруженных проблем
    - Разработка чистой Python версии библиотеки
    - Обеспечение полной кроссплатформенности
