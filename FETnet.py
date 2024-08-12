# coding:utf-8
import codecs
import json
import ssl
import paho.mqtt.client as mqtt
import time
import datetime
import MBus
import schedule


client = mqtt.Client('', True, None, mqtt.MQTTv31)
client.username_pw_set('infilink_ShangriLa2024TPE', 'VbK2rAqE')
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
client.tls_set_context(context)
client.connect('mqtt-device.fetiot3d1.fetnet.net', 8884 , 60)
client.loop_start()
time.sleep(1)
client.on_connect

def FET_Connect():
    try:
        client = mqtt.Client('', True, None, mqtt.MQTTv31)
        client.username_pw_set('infilink_ShangriLa2024TPE', 'VbK2rAqE')
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        client.tls_set_context(context)
        client.connect('mqtt-device.fetiot3d1.fetnet.net', 8884 , 60)
        client.loop_start()
        time.sleep(1)
        client.on_connect
    except:
        pass
    
def FET_Publish(Meter_data):
    now = datetime.datetime.now()
    timestamp = int(now.timestamp())
    
    mod_payload = [
        {"access_token":"{access_token}",
         "app":"ShangriLa2024TPE",
         "type":"{type}",
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
    print (data03)
    print (mod_payload)
    
def do_job():
    PowerMeter = MBus.read_3p3w_meter('COM3',10,1)
    FET_Publish(PowerMeter)

schedule.every(5).seconds.do(do_job)


if __name__ == "__main__":
    while True:
        
        schedule.run_pending()
        time.sleep(1)

