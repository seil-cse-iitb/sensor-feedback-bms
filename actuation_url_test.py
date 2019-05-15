import requests
import json
import time

actuation_url = "http://seil.cse.iitb.ac.in:1337/equipment/actuate/"
HEADERS = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7InVzZXJuYW1lIjoic2VpbEBjc2UuaWl0Yi5hYy5pbiJ9LCJpYXQiOjE1NTUxNjEwNTAsImV4cCI6MTU4NjY5NzA1MH0.D_EnHNCKxwefyW9F3oKO4eDP3WKdJnX6nPF-V9dGp5w"}

print("Turning ON appliance")
on_req = requests.post(url= actuation_url + '17', headers= HEADERS, data= json.dumps({"msg":"S1","state" : True}))
print(on_req.text)
time.sleep(5)
print("Turning OFF appliance") 
off_req = requests.post(url= actuation_url + '17', headers= HEADERS, data= json.dumps({"msg":"S0","state" : False}))
print(off_req.text)