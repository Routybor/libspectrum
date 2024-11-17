
Для начала работы над проектом клонируем репозиторий:

```bash
git clone --recurse-submodules https://github.com/Routybor/libspectrum.git
```

На данный момент проект состоит из 2 частей:

- C++ код, взаимодействующий со спектрометром на низком уровне
- Python код, предоставляющий высокоуровневую абстракцию над спектрометром

Для тестирования библиотеки, ее нужно собрать и установить в вашем virtual environment (или общесистемно).

Python часть библиотеки собирается без проблем, со сборкой C++ кода могут возникнуть трудности в виде волокиты зависимостей и ошибок в процессе самой сборки.

## Разработка в Docker контейнере

Самый простой способ собирать и тестировать библиотеку - использовать заранее сконфигурированный Docker контейнер.

[Docker контейнер на Docker Hub](https://hub.docker.com/repository/docker/ensell84/python-driver-dev/general)

Контейнер содержит virtual environment со всеми необходимыми зависимостями для сборки.

Данный контейнер полностью копирует pipeline для автоматизации который используется в GitHub репозитории для выкладывания библиотеки в pip репозитории.

Находясь в директории с проектом просто запускаем контейнер:

```bash
docker run -v $(pwd):/work -it --rm ensell84/python-driver-dev
```

Из контейнера можем собрать и сразу установить библиотеку в virtual environment:

```bash
pip install .
```

Если же хотим просто собрать wheel бинарник:

```bash
python -m pip wheel . --no-deps
```

Также данный контейнер содержит полный набор зависимостей для сборки документации через `mkdocs build`.

## Разработка на ОС Linux

При сборки на Linux необходимо установить ряд зависимостей:

```bash
apt-get update && apt-get install -y \
    
    libusb-1.0-0-dev \
    libboost-dev \
```

```bash
curl -O https://www.intra2net.com/en/developer/libftdi/download/libftdi1-1.4.tar.bz2 \
    && tar -xf libftdi1-1.4.tar.bz2 \
    && mkdir libftdi1-1.4/build \
    && cd libftdi1-1.4/build \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr .. \
    && make \
    && make install \
    && cd ../.. \
    && rm -rf libftdi1-1.4
```

## Разработка на ОС Windows

`TODO`
