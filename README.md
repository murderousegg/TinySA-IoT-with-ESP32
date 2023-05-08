# TinySA IoT with ESP32
 Python script and ESP32 that can turn TinySA into IoT devices

The goal of this project is to create a platform for measurement devices, that lack internet capabilities, to connect to an IoT network. As a proof of concept, a TinySA is used as a template measurement device. The project consists of 2 main parts: an ESP32 that connects to the measurement device and a server on a raspberry pi 4 model B that hosts a database and dashboards.


# connecting the ESP32 to the TinySA
The ESP32 and the TinySA are connected through a standart UART connection. While there is no such connector on the outside of the TinySA, there are pinholes for it on the motherboard. Pins can be soldered to these holes to allow wires from the ESP32 RX and TX pins to the TX and RX pins of the TinySA. After also connecting ground they should be able to communicate.

Some things to note:
-The TinySA might need to be on newer firmware to change the connection from usb to serial
-Make sure to also select the correct baudrate

# Programming the ESP32
The ESP32 is programmed using the Arduino IDE. Other options are available and might be better, but the Arduino IDE is easier and versitile. To make the ESP32 work with the Arduino IDE, you can follow this guide: https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/. If it shows up on the IDE, you are ready to start. 

The code for the ESP32 is provided in the Arduino folder. Make sure to select the latest version. After downloading, there are some variables that need to be set:
 - MQTT related variables (server, username, password, topic names)
 - wifi credentials
 - baud rate
 - buffer size

Once these are configured the TinySA can be turned on

# Setting up the server
(I assume that your raspberry pi is updated and already has the python dependencies installed.) 
First, download the python script in the python folder. In this script, setup all the required mqtt variables. Make sure your packages are installed and up to date. 

Next, follow this guide to setup all the proper containers: https://www.youtube.com/watch?v=_DO2wHI6JWQ&t=642s . After this setup is completed, you are as good as ready to interact with the data. I recommend setting up a nodered dashboard yourself, or copying the one in the nodered folder. This creates a dashboard through which specific commands can be sent to the TinySA's remotely, and it also allows remote communication with the python script that is running on the server. Grafana can be setup to generate charts from the data, as it is much easier and the interface is much cleaner. 

# final word
Note that many parts of setup are left out. Some errors might pop up somewhere, but they should be easy enough to overcome. Also note that many parts might be more specific to the TinySA and not that easy to convert into something generic. I would love to see an improved, more generic version that can also perform multiple measurements per second. This project has only been tested with 2 devices working simultaniously, but should work on a larger scale as well. (given a better server and more storage)
