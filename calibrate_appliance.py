# Import request and json libraries
import requests
import json
import time
import paho.mqtt.client as mqtt
import paho.mqtt.client as client
from threading import Thread

class GetApplianceList(object):

    def __init__(self):

        # api-endpoint 
        # URL = "http://10.129.149.33:1338/equipment"
        self.URL = "http://seil.cse.iitb.ac.in:1337/equipment"
        self.URL_ZONE = "http://seil.cse.iitb.ac.in:1337/equipmentGroup"
        self.URL_ACTUATE = "http://seil.cse.iitb.ac.in:1337/equipment/actuate/"
        # defining a params dict for the parameters to be sent to the API 
        self.PARAMS = {'location':7} #, 'serial':'F2L'}  # this will change depending upon which location we are callibrating
        self.HEADERS = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7InVzZXJuYW1lIjoic2VpbEBjc2UuaWl0Yi5hYy5pbiJ9LCJpYXQiOjE1NTUxNjEwNTAsImV4cCI6MTU4NjY5NzA1MH0.D_EnHNCKxwefyW9F3oKO4eDP3WKdJnX6nPF-V9dGp5w"}

    def getApplianceDict(self):
        # sending get request and saving the response as response object 
        r = requests.get(url = self.URL, params = self.PARAMS, headers= self.HEADERS) 
        group_appliances = requests.get(url = self.URL_ZONE, params = self.PARAMS, headers= self.HEADERS) 
        
        # extracting data in json format 
        data = r.json()
        # print(type(data))
        # print(data)

        f = open("dump.json",'w')
        f.write(json.dumps(data, indent=4))
        f.close()
        # print (json.dumps(data, indent=4))
        # print(len(data))

        test_dict = {}
        for i in range(0, len(data)):
            test_dict.update({(data[i]["serial"], data[i]["groups"][0]['serial']) : []})

        # print(test_dict)

        # print("Values for grou data-----------------")
        group_data = group_appliances.json()
        # print(type(group_data))

        gf = open("test.json", 'w')
        gf.write((json.dumps(group_data, indent=4)))
        gf.close()
        # print(len(group_data))

        appliance_dict = {}
        group_appliance_dict = {}
        
        for i in range(0, len(group_data)):
            # print(group_data[i]['serial'], group_data[i]['id'])
            group_appliance_dict.update({(group_data[i]['serial'], group_data[i]['id']) : []})

        for i in range(0, len(data)):
            # print(data[i]['serial'], data[i]['id'])
            appliance_dict.update({(data[i]['serial'], data[i]['id']) : []})

        
        # print(appliance_dict)
        # print(group_appliance_dict)

        # print(json.dumps(group_data, indent=4))

        return appliance_dict, group_appliance_dict

    def actuateAppliance(self, appliance_id, command):

        state = False
        if command == 'S1' :
            state = True
        elif command == 'S0' :
            state == False

        requests.post(url=self.URL_ACTUATE + appliance_id, headers= self.HEADERS, data= json.dumps({"msg": command,"state" : state}))

class MqttHandler(object):
    
    MQTT_HOST = "10.129.149.9"
    MQTT_PORT = 1883
    MQTT_CLIENT = "BMS_SENSOR_FEEDBACK"
    MQTT_TOPIC = "actuation/7/#"
    client = mqtt.Client(MQTT_CLIENT)

    def __init__(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_msg
        self.client.connect(self.MQTT_HOST, self.MQTT_PORT, 6)
        mqtt_thread = Thread(target= self.client.loop_forever)
        mqtt_thread.start()

    def on_connect(self,client, userdata, flags, rc):
        print("Connected to MQTT with result " + str(rc))
        client.subscribe(self.MQTT_TOPIC, qos=0)

    def on_msg(self, client, userdata, msg):
        print("%s : %s : %d" %(msg.topic, msg.payload, len(msg.payload)))


def initRoom():

    # Start MQTT server
    mqtt_handler = MqttHandler()

    # Get appliances location and topic
    appliance_properties = GetApplianceList()

    appliance_dict, group_appliance_dict = appliance_properties.getApplianceDict()
    # print(appliance_dict)
    # print(group_appliance_dict)

    # Turning ON/OFF Group appliances in order to capture power signature of a group
    for keys in group_appliance_dict.keys():
        print(keys[1])

    # Turning ON/OFF individual appliance in order to capture power signature
    for keys in appliance_dict.keys():
        print("Turning OFF appliance : ", keys)
        appliance_properties.actuateAppliance(str(keys[1]), 'S0')
        time.sleep(3)
        print("Turning ON appliance : ", keys)
        appliance_properties.actuateAppliance(str(keys[1]), 'S1')
        time.sleep(3)

if __name__ == "__main__":
    initRoom()