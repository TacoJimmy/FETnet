# coding:utf-8
import codecs
import json
import ssl
import paho.mqtt.client as mqtt
import time
import datetime
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
    
def FET_Publish():
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
            {"access_token":"64688f1c2fe5453998c6c475eddbe5ac",
             "app":"ShangriLa2024TPE",
             "type":"electricity_meter",
             "data":[
                 {"timestemp":timestamp,
                  "values":{
                      "voltage_r_s":380
                      }}]}
            ]
    
        data03 = client.publish('/ShangriLa2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
        time.sleep(10)
        print (data03)
        print (mod_payload)
    except:
        pass

def do_job():
    
    FET_Publish()

#schedule.every(5).minutes.do(do_job)
schedule.every(5).seconds.do(do_job)

if __name__ == "__main__":
    while True:
        
        schedule.run_pending()
        time.sleep(1)