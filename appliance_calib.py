# importing the requests library 
import requests
import json
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import time
import MySQLdb as db

# MQTT details
MQTT_HOST = '10.129.149.9'
MQTT_TOPIC = 'actuation/7/#'
MQTT_PORT = 1883
KEEP_ALIVE_TIME = 60

# api-endpoint 
URL = "http://10.129.149.33:1338/equipment"

# defining a params dict for the parameters to be sent to the API 
PARAMS = {'location':7} #, 'serial':'F2L'}  # this will change depending upon which location we are callibrating
HEADERS = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7InVzZXJuYW1lIjoic2VpbEBjc2UuaWl0Yi5hYy5pbiJ9LCJpYXQiOjE1NTUxNjEwNTAsImV4cCI6MTU4NjY5NzA1MH0.D_EnHNCKxwefyW9F3oKO4eDP3WKdJnX6nPF-V9dGp5w"}

# Database details
db_host = "mysql.seil.cse.iitb.ac.in"
db_reader = "reader"
db_writer = "writer"
db_password = "reader"
db_database = "seil_sensor_data"
power_table = "sch_3"

# Power consumption constants for light and fans
W_LIGHT_CONST = 150
W_FAN_CONST = 60
VAR_LIGHT_CONST = -22
VAR_FAN_CONST = 0

mqtt_command = '-1'
appliance_location = '-1'
appliance_type = None

prev_data = {}

# sending get request and saving the response as response object 

def on_connect(client, userdata, flags, rc):
    # client.subscribe(MQTT_TOPIC, qos=0)
    print("Connected with RC " + str(rc))

def on_msg(client, userdata, msg):
    global appliance_location
    global mqtt_command
    global appliance_type
    global PARAMS
    # global prev_data

    # print(msg.payload)
    # print(msg.topic)

    mqtt_command = msg.payload[1]

    topic_details = msg.topic.split("/")
    appliance_location = topic_details[-2]
    
    PARAMS['location'] = topic_details[1]
    PARAMS['serial'] = appliance_location

    print(appliance_location)
    
    if appliance_location[-1] == "F":
        appliance_type = "Fan"
    else:
        appliance_type = "Light"
    
    mqtt_command = msg.payload[1]
    appliance_location = appliance_location[1]

    # print(appliance_location, msg.payload, int(time.time()))

    if (PARAMS['location'], PARAMS['serial']) in prev_data.keys():
        print("Accessing previous data")
        print(prev_data)
    else:
        r = requests.get(url = URL, params = PARAMS, headers= HEADERS) 
        data = r.json()
        prev_data.update({(PARAMS['location'], PARAMS['serial']) : data[0]['id']})
        print("Adding into the database")
        print(prev_data)

    # print(data[0]['id'])

    # print(data[0]['id'])
    
    time.sleep(4)
    getPowerData("\'power_k_seil_l\'", str(int(time.time())))

def getDataDict():
    r = requests.get(url = URL, params = PARAMS, headers= HEADERS) 
    
    # extracting data in json format 
    data = r.json()
    print(type(data))

    f = open("dump.json",'w')
    f.write(json.dumps(data, indent=4))
    f.close()
    # print (json.dumps(data, indent=4))
    print(len(data))

    appliance_data_dict = {}

    for i in range(0, len(data)):
        print(data[i]['serial'])
        appliance_data_dict.update({(data[i]['serial'], data[i]["groups"][0]['serial']) : []})

    # print(appliance_data_dict)
    
    return appliance_data_dict

def calibAppliances():
    print("inside calibAppliance")
    appliance_on = 'S1'
    appliance_off = 'S0'
    mqtt_topic_tx = 'actuation/7/'

    appliance_dict = getDataDict()

    for key in appliance_dict.keys():
        print("\t inside for loop")
        print("\t", key[0])
        appliance = key[0]

        power_on_attributes = []
        power_off_attributes = []

        client.publish(mqtt_topic_tx + appliance + "/", appliance_on, qos=0)
        time.sleep(3)
        power_on_attributes = getPowerData("\'power_k_seil_l\'", str(int(time.time())))
        
        time.sleep(1)

        client.publish(mqtt_topic_tx + appliance + "/", appliance_off, qos=0)
        time.sleep(3)
        power_off_attributes = getPowerData("\'power_k_seil_l\'", str(int(time.time())))
        appliance_dict[key] = power_on_attributes + power_off_attributes
        time.sleep(1)
        print(appliance_dict)

def create_connection(user, pswd):

	con = db.connect(db_host, user, pswd, db_database)
	cursor = con.cursor()

	return con, cursor

def getPowerData(sensor_id, current_time):
    print("Getting power value")
    con, cursor = create_connection(db_reader, db_password)
    sql = "SELECT sensor_id, TS, W, VAR FROM seil_sensor_data.sch_3 where sensor_id = "+ sensor_id + " order by TS desc limit 5;"
    # sql = "SELECT * FROM seil_sensor_data.ds18_13 where sensor_id=\"temp_k_seil_l1_z4\" and TS_RECV > 1519084800 and TS_RECV < 1521504000 order by TS_RECV desc limit 200;"
    # print(sql)
    
    power_data = []
    
    try:
        cursor.execute(sql)
        power_data = cursor.fetchall()

        # for rows in power_data:
        #   print rows

    except Exception as e:
        print("Error: %s" % str(e))
        
    con.close()

    return processPowerData(power_data)

def processPowerData(power_data):
  
    global appliance_location
    global mqtt_command
    global appliance_type

    print("Reactive Power : ",power_data[0][3])
    print("Power : ", power_data[0][2])

    var_change = power_data[0][3] - power_data[4][3]
    w_change = power_data[0][2] - power_data[4][2]

    print("Change in W ", w_change)
    print("Change in VAR ", var_change)

    power_attributes = [w_change, var_change]

    return power_attributes
    # if mqtt_command == '1' and w_change > 90:
    #     print("Light " + appliance_location + " is turned ON")
    # if mqtt_command == '0' and w_change < -90:
    #     print("Light " + appliance_location + " is turned OFF")

    # if mqtt_command == '1' and (w_change < 90 and w_change > 20):
    #     print("Fan " + appliance_location + " is turned ON")
    # if mqtt_command == '0' and (w_change > -90 and w_change < -20):
    #     print("Fan " + appliance_location + " is turned OFF")

    # if -10 < w_change < 10 :
    #     print("PLS CHECK " + appliance_type + " " + appliance_location)

    # print("-------------------------------\n\n")

def initRoom():

    print("Initializing room")
    client.publish("actuation/7/Z1L/", "S0", qos =0)
    client.publish("actuation/7/Z1F/", "S0", qos =0)
    client.publish("actuation/7/Z1A/", "S0", qos =0)

if __name__ == "__main__":
    # print(getDataDict())
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_msg
    client.connect(MQTT_HOST, MQTT_PORT, KEEP_ALIVE_TIME)
    
    initRoom()
    time.sleep(1)
    calibAppliances()
    
    client.loop_forever()