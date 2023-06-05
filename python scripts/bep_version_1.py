#!/usr/bin/env python3

import numpy as np
import time
import random
from paho.mqtt import client as mqtt_client
import pandas as pd
from influxdb import InfluxDBClient

broker = 'broker.emqx.io'
port = 1883
# outputDevice1 = "python/mqtt/inputDevice1"
# inputDevice1 = "python/mqtt/outputDevice1"
input_topics = []
topicmain = "bep/main/main"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'Frank'
password = 'Zenfone8'
userCmd = ""
df_frequencies = pd.DataFrame()
measurement_interval = 8

result_counter = 0

influxclient = InfluxDBClient('131.155.161.195', 8086, 'mydb')
# influxclient.create_database('mydb')
influxclient.switch_database('mydb')
#influxclient.query("DROP SERIES from sweep")

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


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

# def writeCSV(self, x, name):
#     f = open(opt.save, "w")
#     for i in range(len(x)):
#         print("%d, " % self.frequencies[i], "%2.2f" % x[i], file=f)

def on_message(client, userdata, msg):
    if msg.topic == topicmain:
        incomingMessage = msg.payload.decode("utf-8")
        if incomingMessage == "clear database":
            influxclient.query("DROP SERIES from sweep")
        else:
            if "bep/input_devices/" + msg.payload.decode("utf-8") not in input_topics:
                client.subscribe("bep/output_devices/" + incomingMessage)
                input_topics.append("bep/input_devices/" + incomingMessage)
                print("found " + incomingMessage)
        time.sleep(1)
        return
    if msg.topic == "bep/main/interval":
        global measurement_interval
        measurement_interval = msg.payload.decode("utf-8")
        print("measurement interval set to " + msg.payload.decode("utf-8 "))
        return
    try:
        tempList = str(msg.payload.decode("utf-8")).replace('\r', '').split('\n')
    except:
        print("Garbage was probably received")
        return
    ch = tempList.pop()
    actualList = [userCmd]
    # global result_counter
    json_payload = []
    inputTopic = msg.topic.replace("output", "input")
    if "sweep" in tempList[0]:
        client.publish(inputTopic,"frequencies")
        time.sleep(1)
        return
    if "scan " in tempList[0]:
        # print(tempList)
        curtime = time.time_ns()
        x = 1
        for line in tempList[1:]:
            # print(line)
            splitString = line.split()
            # print(line)
            xi = splitString[0]
            # print(xi)
            # print(df_frequencies[inputTopic].values[x])
            # yi = splitString[1]
            if ":." in xi:
                xi = '0'

            data = {
                "measurement": "sweep",
                "tags": {"ticker": inputTopic},
                "time": curtime,
                "fields": {
                    "frequency": df_frequencies[inputTopic].values[x] / 1000000,
                    "gain": float(xi)
                }
            }
            json_payload.append(data)
            curtime = curtime+1
            x = x + 1
        if json_payload[-1]["fields"]["frequency"]*1000000 == json_payload[-1]["fields"]["gain"]:
            #print(json_payload[-1]["fields"]["frequency"])
            #print(json_payload[-1]["fields"]["gain"])
            print("ERROR: sending bad data?")
        #print(json_payload[-1]["fields"]["frequency"]*1000000)
        #print(json_payload[-1]["fields"]["gain"])
        influxclient.write_points(json_payload)
        print("updated " + msg.topic)
        return
    if "frequencies" in tempList[0]:
        if "-:." in tempList[1]:
            tempList[1] = "0"
        if is_number(tempList[1]):
            while not is_number(tempList[-1]):
                del tempList[-1]
            for x in list(map(float, tempList[1:])):
                actualList.append(x)
            df_frequencies[inputTopic] = actualList
            # result_counter = result_counter + 1
            print("frequencies updated")
            return
    else:
        print("Don't know this output")
        return
    # print("last line")

class tinySA:
    def __init__(self, dev=None):
        # self.dev = dev or getport()
        self.serial = None
        self._frequencies = None
        self.points = 101

    @property
    def frequencies(self):
        return self._frequencies

    def set_frequencies(self, start=1e6, stop=350e6, points=None):
        if points:
            self.points = points
        self._frequencies = np.linspace(start, stop, self.points)

    def send_command(self, cmd, topic):
        global userCmd
        userCmd = cmd
        client.publish(topic, cmd)

    def fetch_data(self, inputTopic):
        # global result_counter
        # prev = result_counter
        while inputTopic not in df_frequencies:
            pass
        result = df_frequencies[inputTopic]
        return result.to_numpy()

    def fetch_frequencies(self, topic):
        self.send_command("frequencies", topic)
        data = self.fetch_data(topic)
        self._frequencies = data[1:]

    def animate(self):
        # self.scan(topicnumber)
        for i in input_topics:
            while i not in df_frequencies:
                self.fetch_frequencies(i)
                time.sleep(1)
            # freqs = self._frequencies
        #time.sleep(1)
        for i in input_topics:
            self.send_command("scan %d %d 290 2" % (df_frequencies[i].iloc[1], df_frequencies[i].iloc[-1]), i)

        time.sleep(float(measurement_interval))




if __name__ == '__main__':
    client = connect_mqtt()
    client.on_message = on_message
    # print("help")
    client.subscribe(topicmain)
    client.subscribe("bep/main/interval")
    # client.publish(topicout, "mode input high".encode())
    client.loop_start()
    client.publish("A", "restart")
    time.sleep(1)
    myTinySA = tinySA()
    myTinySA.__init__()
    while 1:
        if len(input_topics) > 0:
            myTinySA.animate()
