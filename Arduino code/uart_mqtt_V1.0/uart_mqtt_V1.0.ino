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
  -this setup struggles with communicating large streams of data:
   for instance, many measurements are lost when asking for data
  -wifi is not secure at all, NEVER store your passwords unencrypted in a text file
   I'm just lazy right now
  

  VERSION--V1.01 : (maybe fixed large datastream issue?)
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <Arduino.h>
//define GPIO pins for UART communication
#define UART_RX_PIN 44 // GPIO2
#define UART_TX_PIN 42 // GPIO4

//define wificlient for esp32
WiFiClient espClient;
//define client for mqtt communication
PubSubClient mqttClient(espClient);
// mqtt credentials
const char *mqtt_broker = "broker.emqx.io";
const char *topicin = "python/mqtt/testin";
const char *topicout = "python/mqtt/testout";
const char *mqtt_username = "Frank";
const char *mqtt_password = "Zenfone8";
const int mqtt_port = 1883;
//WIFI credentials here
String APName = "AndroidAP85af";
String WIFIpsk = "kaqu2459";

char incomingByte[50]; //create variable to store incoming MQTT data

// callback for incoming mqtt messages, prints them over the UART serial port
void callback(char* topic, byte* payload, unsigned int length) {
  //add if statement here that checks for correct to
  for (int i=0;i<length;i++) {
   incomingByte[i] =  (char)payload[i];
   incomingByte[i+1]=(char)0;
   }
   Serial.println(incomingByte); //note: dubbelcheck if this should be Serial1? 
  }


void setup()
{
  Serial.begin(115200); //begin serial ports
  Serial1.begin(115200, SERIAL_8N1,
                UART_RX_PIN,
                UART_TX_PIN);
  pinMode(40, OUTPUT); //for debugging led
  WiFi.disconnect();
  delay(3000); //give time for wifi to start up
  WiFi.begin(APName, WIFIpsk); //start up wifi with credentials
  while ((!(WiFi.status() == WL_CONNECTED))){
    delay(300); //loop while not connected
  }
  mqttClient.setServer(mqtt_broker, mqtt_port); //setup mqtt broker
  mqttClient.setCallback(callback); //define the callback function for incoming messages
  while (!mqttClient.connected()) { //start MQTT connection
    String client_id = String(WiFi.macAddress());
      if (mqttClient.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
      } else {
          delay(2000);
      }
  }
 mqttClient.publish(topicout, "Hello! I am ESP32"); //publish a test message to let the pc know it is live
 mqttClient.subscribe(topicin);
}

void loop()
{
  mqttClient.loop(); //keep listening on mqtt channel
  while (Serial1.available() > 0){ //loop for publishing incoming data on rx pins to a topic
    digitalWrite(40,1);
    String data = Serial1.readString());
    const char *payload = data.c_str();
    if(data.length()>>254){
      mqttClient.setBufferSize(8192); //test: temporarily increase buffer size for large messages
    }
    mqttClient.publish(topicout, payload);
    mqttClient.setBufferSize(256);
  }
  digitalWrite(40,0);
} 