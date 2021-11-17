# coding:utf-8

import json
import ssl
import time
import paho.mqtt.client as mqtt
# import jsonpath
import PW_meter
import AC_ctrl
# constants

import codecs

name01 = '2164-ACInf1-48F31BE2'
name02 = '2164-ACInf2-544D6194' 
name03 = '2164-ACInf3-F3A5B00D'
mqtt_passwd = ''

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # subscribe
        client.subscribe('v1/devices/me/attributes', 1)
        time.sleep(3)
        # publish
    else:
        client.disconnect()
        
def on_message(client, userdata, msg):
    AC_Power = msg.payload
    j = json.loads(AC_Power)
    print(j)
    print(type(j))
    print(j['AC_power'])
    print(type(j['AC_power']))
    

def Get_ACCtrl(client, userdata, flags, rc):
    
    if rc == 0:
        # subscribe
        client.subscribe('v1/devices/me/attributes', 1)
        time.sleep(3)
    else:
        client.disconnect()
        
        
def send_MainPW(client, userdata, flags, rc):
    MainPW = PW_meter.read_3p3w_meter('COM3',1) # main power
    # MainPW = (0,0,0,0,0,0,0,0)
    MainPW_payload = {
        "emsstorelvoltage": MainPW[0],"emsstorercurrentA":MainPW[1],"emsstorercurrentB":MainPW[2],"emsstorercurrentC":MainPW[3],
        "emsstorepower": MainPW[4],"emsstoreopf": MainPW[5], "emsstorecumulativeelectricityconsumption": MainPW[6],
        "emsstoretype": "三相三線","emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":MainPW[7]
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(MainPW_payload))
        time.sleep(3)
    else:
        client.disconnect()
        
def send_AC01Meter(client, userdata, flags, rc):
    MainPW = PW_meter.read_1p2w_meter('COM3',2,1) # main power
    MainPW_payload = {
        "emsstoreacmvoltage": MainPW[0],"emsstoreacmcurrent":MainPW[1],"emsstoreacmpower":MainPW[2],"emsstoreacmpf":MainPW[3],
        "emsstoreacmconsumption": MainPW[4],
        "emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":MainPW[5]
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(MainPW_payload))
        time.sleep(3)
    else:
        client.disconnect()

def send_AC02Meter(client, userdata, flags, rc):
    MainPW = PW_meter.read_1p2w_meter('COM3',3,1) # main power
    MainPW_payload = {
        "emsstoreacmvoltage": MainPW[0],"emsstoreacmcurrent":MainPW[1],"emsstoreacmpower":MainPW[2],"emsstoreacmpf":MainPW[3],
        "emsstoreacmconsumption": MainPW[4],
        "emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":MainPW[5]
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(MainPW_payload))
        time.sleep(3)
    else:
        client.disconnect()
        
def send_AC03Meter(client, userdata, flags, rc):
    MainPW = PW_meter.read_1p2w_meter('COM3',4,1) # main power
    MainPW_payload = {
        "emsstoreacmvoltage": MainPW[0],"emsstoreacmcurrent":MainPW[1],"emsstoreacmpower":MainPW[2],"emsstoreacmpf":MainPW[3],
        "emsstoreacmconsumption": MainPW[4],
        "emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":MainPW[5]
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(MainPW_payload))
        time.sleep(3)
    else:
        client.disconnect()


    
def connect_storemeter(token):
    FETnet_token = token 
    FETnet_passwd = ''
    client = mqtt.Client('', True, None, mqtt.MQTTv31)
    client.username_pw_set(FETnet_token, FETnet_passwd)
    
    
    # the key steps here
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # if you do not want to check the cert hostname, skip it
    # context.check_hostname = False
    client.tls_set_context(context)
    client.connect("portal.cat2.fetnet.net", 1883, 60)
    client.loop_start()
    client.on_connect = send_MainPW
    client.loop_stop()
    client.disconnect()
    #client.loop_forever()

         
def connect_AC01Meter(meter_token):
    #FETnet_token = '2164-STOREM-30D422AD' 
    FETnet_passwd = ''
    client = mqtt.Client('', True, None, mqtt.MQTTv31)
    client.username_pw_set(meter_token, FETnet_passwd)
    
    
    # the key steps here
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # if you do not want to check the cert hostname, skip it
    # context.check_hostname = False
    client.tls_set_context(context)
    client.connect("portal.cat2.fetnet.net", 1883, 60)
    client.loop_start()
    if meter_token == '2164-ACMtr1-590263AF':
        client.on_connect = send_AC01Meter
    elif meter_token == '2164-ACMtr2-A0FA49D0':
        client.on_connect = send_AC02Meter
    elif meter_token == '2164-ACMtr3-149F5F52':
        client.on_connect = send_AC03Meter
    client.loop_stop()
    client.disconnect()
    #client.loop_forever()

def send_AC01Fullstatus(client, userdata, flags, rc):
    AC_Status = AC_ctrl.AC_ReadFullFunction('COM10',1) # main power
    AC_payload = {
        "emsstoreairconditioningstatus": AC_Status[0],
        "emsstoreoperationmode":AC_Status[1],
        "emsstorewindspeed":AC_Status[2],
        "emsstoresettemperature":AC_Status[3],
        "emsstoreroomtemperature": AC_Status[4],
        "emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":1
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(AC_payload))
        time.sleep(3)
    else:
        client.disconnect()
def send_AC02Fullstatus(client, userdata, flags, rc):
    AC_Status = AC_ctrl.AC_ReadFullFunction('COM10',1) 
    AC_payload = {
        "emsstoreairconditioningstatus": AC_Status[0],
        "emsstoreoperationmode":AC_Status[1],
        "emsstorewindspeed":AC_Status[2],
        "emsstoresettemperature":AC_Status[3],
        "emsstoreroomtemperature": AC_Status[4],
        "emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":1
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(AC_payload))
        time.sleep(3)
    else:
        client.disconnect()
        
def send_AC03Fullstatus(client, userdata, flags, rc):
    AC_Status = AC_ctrl.AC_ReadFullFunction('COM10',1) 
    AC_payload = {
        "emsstoreairconditioningstatus": AC_Status[0],
        "emsstoreoperationmode":AC_Status[1],
        "emsstorewindspeed":AC_Status[2],
        "emsstoresettemperature":AC_Status[3],
        "emsstoreroomtemperature": AC_Status[4],
        "emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":1
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(AC_payload))
        time.sleep(3)
    else:
        client.disconnect()

def send_ACPW_Infor(client, userdata, flags, rc):
    AC_Status = AC_ctrl.AC_ReadFullFunction('COM10',1) # main power
    AC_payload = {
        "emsstoreairconditioningstatus": AC_Status[0],
        "emsstoreoperationmode":AC_Status[1],
        "emsstorewindspeed":AC_Status[2],
        "emsstoresettemperature":AC_Status[3],
        "emsstoreroomtemperature": AC_Status[4],
        "emsvendorinfo":"歐陸通風-ADTEK-AEMDR TEL:0935-534163",
        "emsdevicealive":1
        }   

    if rc == 0:
        client.publish('v1/devices/me/telemetry',json.dumps(AC_payload))
        time.sleep(3)
    else:
        client.disconnect()





def connect_ACstatus(meter_token):
    #FETnet_token = '2164-STOREM-30D422AD' 
    FETnet_passwd = ''
    client = mqtt.Client('', True, None, mqtt.MQTTv31)
    client.username_pw_set(meter_token, FETnet_passwd)
    
    
    # the key steps here
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # if you do not want to check the cert hostname, skip it
    # context.check_hostname = False
    client.tls_set_context(context)
    client.connect("portal.cat2.fetnet.net", 1883, 60)
    client.loop_start()
    if meter_token == '2164-ACInf1-48F31BE2':
        client.on_connect = send_AC01Fullstatus
    elif meter_token == '2164-ACInf2-544D6194':
        client.on_connect = send_AC02Fullstatus
    elif meter_token == '2164-ACInf3-F3A5B00D':
        client.on_connect = send_AC03Fullstatus
    client.loop_stop()
    client.disconnect()
    
def connect_ACPWstatus(meter_token):
    #FETnet_token = '2164-STOREM-30D422AD' 
    FETnet_passwd = ''
    client = mqtt.Client('', True, None, mqtt.MQTTv31)
    client.username_pw_set(meter_token, FETnet_passwd)
    
    
    # the key steps here
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # if you do not want to check the cert hostname, skip it
    # context.check_hostname = False
    client.tls_set_context(context)
    client.connect("portal.cat2.fetnet.net", 1883, 60)
    client.loop_start()
    if meter_token == '2164-ACInf1-48F31BE2':
        client.on_connect = send_AC01Fullstatus
    elif meter_token == '2164-ACInf2-544D6194':
        client.on_connect = send_AC02Fullstatus
    elif meter_token == '2164-ACInf3-F3A5B00D':
        client.on_connect = send_AC03Fullstatus
    client.loop_stop()
    client.disconnect()
'''
while True:
    
    connect_storemeter('2419-STOREM-F85F74E9')
    
    # send the meter Data
    connect_storemeter()
    connect_AC01Meter('2164-ACMtr1-590263AF')
    connect_AC01Meter('2164-ACMtr2-A0FA49D0')
    connect_AC01Meter('2164-ACMtr3-149F5F52')
    # send the AC Status
    time.sleep(3)
    connect_ACstatus('2164-ACInf1-48F31BE2')
    time.sleep(3)
    connect_ACstatus('2164-ACInf2-544D6194')
    time.sleep(3)
    connect_ACstatus('2164-ACInf3-F3A5B00D')
    
    client = mqtt.Client('', True, None, mqtt.MQTTv31)
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    client.tls_set_context(context)

    client.username_pw_set(name01, mqtt_passwd)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("portal.cat2.fetnet.net", 1883, 60)

    client.username_pw_set(name02, mqtt_passwd)
    client.on_connect = on_connect
    client.on_message = on_message
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    client.connect("portal.cat2.fetnet.net", 1883, 60)

    client.username_pw_set(name03, mqtt_passwd)
    client.on_connect = on_connect
    client.on_message = on_message
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    client.connect("portal.cat2.fetnet.net", 1883, 60)
    time.sleep(3)
    client.loop()
    while True:
        client.loop()
    client.loop_stop
    client.disconnect
    
    time.sleep(3)
    print("here");
''' 
