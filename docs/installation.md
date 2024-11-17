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
      pip install vmk-spectrum
    ```
1. Изменить права доступа к USB устройству (необходимо для использования библиотеки не из-под root'а)  
   ```
   echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014",  MODE="0666"' | sudo tee /etc/udev/rules.d/69-spectrometer.rules
   sudo udevadm control --reload
   ```

## Windows
1. Установить [драйвер FTDI](https://ftdichip.com/wp-content/uploads/2021/08/CDM212364_Setup.zip) (Если на компьютере ранее работал `Atom`, шаг можно пропустить)
3. Установить [Распространяемый пакет Visual C++ для Visual Studio 2015](https://www.microsoft.com/ru-RU/download/details.aspx?id=48145)
3. Установить **64-битный** Python (минимальная версия - 3.10)  
1. Установить библиотеку  
    ```
   pip install vmk-spectrum
    ```  
   

