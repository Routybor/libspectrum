---
hide:
- navigation
---
# Установка библиотеки
## Linux
(команды приведены для Ubuntu 22.04 LTS)  


1. Установить python и pip (минимальная версия - 3.10)  
    ```
    sudo apt install python3 python3-pip libxcb-xinerama0
    ```  
    `libxcb-xinerama0` нужна только для работы демо на Ubuntu  
1. Установить библиотеку  
    ```
      pip3 install --user https://github.com/leadpogrommer/libspectrum/releases/download/latest/pyspectrum-0.0.2-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
    ```  
   Ссылку на последнюю версию можно взять [здесь](https://github.com/leadpogrommer/libspectrum/releases). Необходимо использовать версию,
   соответствующую версии Python (cp310 - Python 3.10, cp311 - Python 3.11 etc).
1. Изменить права доступа к USB устройству (необходимо для использования библиотеки не из-под root'а)  
   ```
   echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014",  MODE="0666"' | sudo tee /etc/udev/rules.d/69-spectrometer.rules
   sudo udevadm control --reload
   ```

## Windows
1. Установить [драйвер FTDI](https://ftdichip.com/wp-content/uploads/2021/08/CDM212364_Setup.zip) (Если на компьютере ранее работал `Atom`, шаг можно пропустить)
3. Установить [Распространяемый пакет Visual C++ для Visual Studio 2015](https://www.microsoft.com/ru-RU/download/details.aspx?id=48145)
3. Установить Python (минимальная версия - 3.10)  
1. Установить библиотеку  
    ```
    pip3 install --user https://github.com/leadpogrommer/libspectrum/releases/download/latest/pyspectrum-0.0.2-cp310-cp310-win_amd64.whl
    ```  
   Ссылку на последнюю версию можно взять [здесь](https://github.com/leadpogrommer/libspectrum/releases). Необходимо использовать версию,
   соответствующую версии Python (cp310 - Python 3.10, cp311 - Python 3.11 etc).

