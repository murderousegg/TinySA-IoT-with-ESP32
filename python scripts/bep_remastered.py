#!/usr/bin/env python3

#########################################################################
#   This program was written for my Bachelor End Project. It serves as  #
#   a proof of concept for making a tinySA (but hopefully other         #
#   devices as well) part of an IoT of measurement devices, even        #
#   absent internet function. This script is meant for the server side  #
#   and asks for data from the tinySA, which is then stored in an       #
#   InfluxDB database. The data can then be worked with remotely        #
#   through Grafana and Nodered.                                        #
#                                                                       #
#########################################################################
import numpy as np
import time
import random
from paho.mqtt import client as mqtt_client
import pandas as pd
from influxdb import InfluxDBClient

#setup broker
broker = 'broker.emqx.io'
port = 1883
input_topics = []       #create empty list to store devices
topicmain = "bep/main/main"
client_id = f'python-mqtt-{random.randint(0, 1000)}' #generate random id
username = 'Frank'              #broker credentials
password = 'Zenfone8'
userCmd = ""                    #variable to store last command
df_frequencies = pd.DataFrame() #create df to store frequencies
measurement_interval = 8        #set default measurement interval

#setup influxdb database
influxclient = InfluxDBClient('131.155.161.195', 8086, 'mydb')  #check for updated ip adress!
influxclient.switch_database('mydb')

#function to find out if something is a number to prevent errors
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#default connect to mqtt function
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

#callback for when message is received
def on_message(client, userdata, msg):
    if msg.topic == topicmain:  #check if message is from main topic
        incomingMessage = msg.payload.decode("utf-8")
        if incomingMessage == "clear database":
            influxclient.query("DROP SERIES from sweep")    #clear database
        else:   #store mac address as topic in topics and subscribe
            if "bep/input_devices/" + msg.payload.decode("utf-8") not in input_topics:
                client.subscribe("bep/output_devices/" + incomingMessage)
                input_topics.append("bep/input_devices/" + incomingMessage)
                print("found " + incomingMessage)
        time.sleep(1)
        return
        
    if msg.topic == "bep/main/interval":    #change measurement interval
        global measurement_interval
        measurement_interval = msg.payload.decode("utf-8")
        print("measurement interval set to " + msg.payload.decode("utf-8 "))
        return
        
    try:    #prevent errors for when garbage is transmitted
        tempList = str(msg.payload.decode("utf-8")).replace('\r', '').split('\n')
    except:
        print("Garbage was probably received, check baudrate")
        return
        
    ch = tempList.pop() #remove ch> from list
    json_payload = []   #create list to store dicts with data
    inputTopic = msg.topic.replace("output", "input")   #get correct input topic from output topic
    if "sweep" in tempList[0]:  #measurement frequencies have changed
        client.publish(inputTopic,"frequencies")    #update frequencies
        time.sleep(1)   #extra sleep to prevent errors
        return
        
    if "scan " in tempList[0]:  #got new measurements
        curtime = time.time_ns() #set timestamp for when measurements were retrieved
        x = 1   #used for selecting frequency from dataframe
        for line in tempList[1:]:   #loop over results line by line
            splitString = line.split()  #split line to get gains
            xi = splitString[0] #store gain in xi
            if ":." in xi:  #corrects when first result is :. or -:.
                xi = '0'
            data = {        #store gain and frequency in a dictionary
                "measurement": "sweep",
                "tags": {"ticker": inputTopic},
                "time": curtime,
                "fields": {
                    "frequency": df_frequencies[inputTopic].values[x] / 1000000,
                    "gain": float(xi)
                }
            }
            json_payload.append(data)
            curtime = curtime+1 #influxdb doesn't handle duplicate timestamps
            x = x + 1
        #sometimes error occurs where gain=frequency
        if json_payload[-1]["fields"]["frequency"]*1000000 == json_payload[-1]["fields"]["gain"]:
            print("ERROR: sending bad data?")
            return
        influxclient.write_points(json_payload) #write to database
        print("updated " + msg.topic)
        return
        
    if "frequencies" in tempList[0]:
        actualList = []
        if "-:." in tempList[1]:    #correct for bug in transmission
            tempList[1] = "0"
        if is_number(tempList[1]):
            while not is_number(tempList[-1]):
                del tempList[-1]    #delete last entries that arent numbers
            for x in list(map(float, tempList[1:])):    #turn list of frequencies into floats and loop over them
                actualList.append(x)
            df_frequencies[inputTopic] = actualList #update frequencies
            print("frequencies updated")
            return
            
    else:
        print("Don't know this output") #when garbage is received
        return

#request data from all tinySA's (note: tested with only 2!!!!)
def animate():
    for i in input_topics:  #loop over tinySA's
        while i not in df_frequencies:  #check if the frequency range is known
            client.publish(i, "frequencies")    #update frequency range
            time.sleep(1)   #safety sleep before sending commands too fast
    for i in input_topics:  #loop over tinySA's
        firstFrequency=df_frequencies[i].iloc[1]    #get start frequency
        lastFrequency=df_frequencies[i].iloc[-1]    #get stop frequency
        self.send_command("scan %d %d 290 2" % (firstFrequency, lastFrequency), i)  #get scan results
    time.sleep(float(measurement_interval)) #interval between measurements, set by nodered

if __name__ == '__main__':
    #setup process
    client = connect_mqtt() #connect to mqtt
    client.on_message = on_message  #set callback for when message is received
    client.subscribe(topicmain) #subscribe to topic where MAC addresses are posted
    client.subscribe("bep/main/interval")   #subscribe to topic where interval is updated
    client.loop_start() #start mqtt loop
    client.publish("A", "restart")  #let running ESP32's know the program restarted
    time.sleep(1)   #give everything time to settle
    while 1:
        if len(input_topics) > 0:   #start as soon as a tinySA is discovered
            animate()
