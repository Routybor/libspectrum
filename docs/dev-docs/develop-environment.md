
Для начала работы над проектом клонируем репозиторий:

```bash
git clone --recurse-submodules https://github.com/Routybor/libspectrum.git
```

На данный момент проект состоит из 2 частей:

- C++ код, обеспечивающий низкоуровневое взаимодействие со спектрометром.
- Python код, предоставляющий высокоуровневую абстракцию над спектрометром.

Для тестирования библиотеки, ее нужно собрать и установить в вашем virtual environment (или общесистемно).

Python часть библиотеки собирается без проблем, однако сборка C++ кода может вызвать трудности, связанные с зависимостями и ошибками в процессе сборки.

## Разработка в Docker контейнере

Наиболее простой способ собрать и протестировать библиотеку — использовать предварительно сконфигурированный Docker контейнер.

[Docker контейнер на Docker Hub](https://hub.docker.com/repository/docker/ensell84/python-driver-dev/general)

Контейнер содержит virtual environment со всеми необходимыми зависимостями для сборки.

Этот контейнер полностью воспроизводит pipeline в GitHub workflow.

Находясь в директории с проектом просто запускаем контейнер:

```bash
docker run -v $(pwd):/work -it --rm ensell84/python-driver-dev
```

Из контейнера можно собрать и сразу установить библиотеку в virtual environment:

```bash
pip install .
```

Если требуется только сборка wheel бинарника:

```bash
python -m pip wheel . --no-deps
```

Контейнер также содержит полный набор зависимостей для сборки документации через `mkdocs build`.
 
## Разработка на ОС Linux

Протестированно и гарантированно работает на Linux Ubuntu 22.04.

Для сборки на Ubuntu необходимо установить следующие зависимости:

```bash
apt-get update && apt-get install -y libftdipp1-dev libusb-1.0-0-dev libboost-dev
```

Также в системе должен быть установлен `python`:

```bash
apt-get install -y python3 python3-venv python3-dev
```

Важно установить `python3-dev`, без него библиотека не соберется.

Вместо установки `libftdipp1-dev` можно собрать библиотеку вручную (так и происходит в GitHub workflows и в Docker контейнере):

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

Рекомендуется создать `virtual environment` в директории проекта и затем собирать библиотеку в ней:

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install .
```

Все необходимые pip зависимости будут автоматически скачаны и установлены.

Если требуется сборка wheel бинарника:

```bash
python -m pip wheel .
```

## Разработка на ОС Windows

`TODO`
