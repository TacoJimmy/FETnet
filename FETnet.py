# coding:utf-8
import codecs
import json
import ssl
import paho.mqtt.client as mqtt
import time
import datetime
import MBus
import schedule

# dev
client = mqtt.Client('', True, None, mqtt.MQTTv31)
client.username_pw_set('infilink_ShangriLa2024TPE', 'wCGTd25n')
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.connect('mqtt-device.fetiot3s1.fetnet.net', 8884 , 60)
client.loop_start()
time.sleep(1)
client.on_connect

def FET_Connect():
    try:
        client = mqtt.Client('', True, None, mqtt.MQTTv31)
        client.username_pw_set('infilink_ShangriLa2024TPE', 'wCGTd25n')
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.connect('mqtt-device.fetiot3s1.fetnet.net', 8884 , 60)
        client.loop_start()
        time.sleep(1)
        client.on_connect
    except:
        pass
    

def FET_Publish_Product(Meter_data,access_token):
    try:
        now = datetime.datetime.now()
        timestamp = int(now.timestamp())
        client = mqtt.Client('', True, None, mqtt.MQTTv31)
        client.username_pw_set('infilink_ShangriLa2024TPE', '5WufQ879')
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.connect('mqtt-device.fetiot3p1.fetnet.net', 8884 , 60)
        client.loop_start()
        time.sleep(1)
        client.on_connect
        time.sleep(1)
        mod_payload = [
            {"access_token":access_token,
             "app":"ShangriLa2024TPE",
             "type":"electricity_meter",
             "data":[
                 {"timestemp":timestamp,
                  "values":{
                      "voltage_r_s":Meter_data[1],
                      "voltage_s_t":Meter_data[2],
                      "voltage_t_r":Meter_data[3],
                      "voltage_line_avg":Meter_data[4],
                      "current_r":Meter_data[5],
                      "current_s":Meter_data[6],
                      "current_t":Meter_data[7],
                      "current_phase_avg":Meter_data[8],
                      "frequency":Meter_data[0],
                      "power": Meter_data[9],
                      "power_kvar":Meter_data[10],
                      "energy":Meter_data[14],
                      "immediate_demand":Meter_data[13],
                      "pf":Meter_data[12],
                      "alive":Meter_data[16],
                      "type":"三相三線"
                      }}]}
            ]
    
        data03 = client.publish('/ShangriLa2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
        time.sleep(10)
        print (data03)
        print (mod_payload)
    except:
        pass

def FET_Publish_Station(Meter_data,access_token):
    try:
        now = datetime.datetime.now()
        timestamp = int(now.timestamp())
        client = mqtt.Client('', True, None, mqtt.MQTTv31)
        client.username_pw_set('infilink_ShangriLa2024TPE', 'wCGTd25n')
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.connect('mqtt-device.fetiot3s1.fetnet.net', 8884 , 60)
        client.loop_start()
        time.sleep(1)
        client.on_connect
        time.sleep(1)
        mod_payload = [
            {"access_token":access_token,
             "app":"ShangriLa2024TPE",
             "type":"electricity_meter",
             "data":[
                 {"timestemp":timestamp,
                  "values":{
                      "voltage_r_s":Meter_data[1],
                      "voltage_s_t":Meter_data[2],
                      "voltage_t_r":Meter_data[3],
                      "voltage_line_avg":Meter_data[4],
                      "current_r":Meter_data[5],
                      "current_s":Meter_data[6],
                      "current_t":Meter_data[7],
                      "current_phase_avg":Meter_data[8],
                      "frequency":Meter_data[0],
                      "power": Meter_data[9],
                      "power_kvar":Meter_data[10],
                      "energy":Meter_data[14],
                      "immediate_demand":Meter_data[13],
                      "pf":Meter_data[12],
                      "alive":Meter_data[16],
                      "type":"三相三線"
                      }}]}
            ]
    
        data03 = client.publish('/ShangriLa2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
        time.sleep(10)
        print (data03)
        print (mod_payload)
    except:
        pass

def do_job():
    
    PowerMeter = MBus.read_3p3w_meter('/dev/ttyS3',30,1)
    FET_Publish_Product(PowerMeter,"4ebb30b3db7546b194334f7a0188b487")
    time.sleep(3)
    FET_Publish_Station(PowerMeter,"4ebb30b3db7546b194334f7a0188b487")
    time.sleep(3)
    PowerMeter = MBus.read_3p3w_meter('/dev/ttyS3',31,1)
    FET_Publish_Product(PowerMeter,"84f4d26e14bc45ddab170a48b9cc1e10")
    time.sleep(3)
    FET_Publish_Station(PowerMeter,"84f4d26e14bc45ddab170a48b9cc1e10")
    time.sleep(3)
    PowerMeter = MBus.read_3p3w_meter('/dev/ttyS3',32,1)
    FET_Publish_Product(PowerMeter,"99b270cf07544505a91fe924062af584")
    time.sleep(3)
    FET_Publish_Station(PowerMeter,"99b270cf07544505a91fe924062af584")
    time.sleep(3)

#schedule.every(5).minutes.do(do_job)
schedule.every(60).seconds.do(do_job)

if __name__ == "__main__":
    while True:
        
        schedule.run_pending()
        time.sleep(1)