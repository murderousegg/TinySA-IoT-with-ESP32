/*
---CODE FOR SETTING UP AN MQTT BROKER ON ESP32, AND INTERFACING WITH A UART CONNECTION---
This code was written by Frank Overbeeke, and is available for public use without license. 
Feel free to credit me in future projects. 

This program sets up a wifi network, and then connects to an MQTT broker. It is still a work in
progress, but works decently well. The ESP acts as a middle man in communication between a 
remote pc and any device that has a UART port and supports text commands. Some things to note

- only tested on tinySA as of 03-11-2023
- some things need to be adjusted to create a network:
  -create different MQTT topics for different esp nodes
  -wifi is not secure at all, NEVER store your passwords unencrypted in a text file
   I'm just lazy right now
  

  VERSION--V1.4 : retransmits mac on restart of server, increased baudrate to 460800
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <Arduino.h>
//define GPIO pins for UART communication
#define UART_RX_PIN 44  // GPIO2
#define UART_TX_PIN 42  // GPIO4

//define wificlient for esp32
WiFiClient espClient;
//define client for mqtt communication
PubSubClient mqttClient(espClient);
String mac_address_string = WiFi.macAddress();
char mac_address[32];
// mqtt credentials
const char *mqtt_broker = "broker.emqx.io";
const char *topicmain = "bep/main/main";
char topicin[100];
char topicout[100];
// strcat(topicout, mac_address.c_str());
const char *mqtt_username = "Frank";
const char *mqtt_password = "Zenfone8";
const int mqtt_port = 1883;
//WIFI credentials here
const char *APName = "AndroidAP85af";
const char *WIFIpsk = "kaqu2459";
const int BUFFER_SIZE = 15000; //buffer for received messages
char *restart = "restart";     //for when restart command is received
int BAUDRATE = 460800;         //higher baudrate > faster update but also unstable
byte buf[BUFFER_SIZE];         //create empty byte array of size BUFFER_SIZE

char incomingByte[50];  //create variable to store incoming MQTT data

// callback for incoming mqtt messages, prints them over the UART serial port
void callback(char *topic, byte *payload, unsigned int length) {
  //store incoming data character by character into array and force it to end with a 0
  for (int i = 0; i < length; i++) {  
    incomingByte[i] = (char)payload[i];
    incomingByte[i + 1] = (char)0;
  }
  if(strcmp(restart,incomingByte)==0){
      mqttClient.publish(topicmain, mac_address);  //publish a test message to let the pc know it is live
      return; //return without sending to tinySA
  }
  //send data to tinySA
  Serial.println(incomingByte);
}


void setup() {
  Serial.begin(BAUDRATE);  //begin serial ports
  Serial1.begin(BAUDRATE, SERIAL_8N1,
                UART_RX_PIN,
                UART_TX_PIN);
  Serial1.setTimeout(2000);
  Serial.setTimeout(2000);
  pinMode(40, OUTPUT);  //for debugging led
  WiFi.disconnect();
  delay(3000);                  //give time for wifi to start up
  WiFi.begin(APName, WIFIpsk);  //start up wifi with credentials
  while ((!(WiFi.status() == WL_CONNECTED))) {
    delay(300);  //loop while not connected
  }
  mqttClient.setServer(mqtt_broker, mqtt_port);  //setup mqtt broker
  mqttClient.setCallback(callback);              //define the callback function for incoming messages
  while (!mqttClient.connected()) {              //start MQTT connection
    String client_id = String(WiFi.macAddress());
    if (mqttClient.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
    } else {
      delay(2000);
    }
  }
  //bunch of code to create topics with ESP32's MAC address
  mac_address_string.toCharArray(mac_address, mac_address_string.length()+1);
  strcpy(topicin, "bep/input_devices/");
  strcat(topicin, mac_address);
  strcpy(topicout, "bep/output_devices/");
  strcat(topicout, mac_address);
  //publish MAC address to main topic for server to see
  mqttClient.publish(topicmain, mac_address);  //publish a test message to let the pc know it is live
  //subscribe to personal input topic
  mqttClient.subscribe(topicin);
  //subscribe to topic used for the restart command
  mqttClient.subscribe("bep/main/reset");
  mqttClient.setBufferSize(20000);  //Set larger buffersize for large datastreams (little penalty on speed)
}

void loop() {
  mqttClient.loop();                 //keep listening on mqtt channel
  if (Serial1.available() > 1) {  //loop for publishing incoming data on rx pins to a topic
    digitalWrite(40, 1);  //turn on debug led
    //read bytes: beware that if your incoming data exceeds the buffer size you will probably receive weird data
    int rlen = Serial1.readBytesUntil('>', buf, BUFFER_SIZE); //read until tinySA asks for new command ('>' not included in buffer)
    mqttClient.publish(topicout, buf, rlen);  //publish data to personal output topic
    digitalWrite(40,0); //turn off debug led
    memset(buf, 0, sizeof(buf)); //make sure buffer is empty for next data
  }
}