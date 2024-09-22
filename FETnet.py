# coding:utf-8
import codecs
import json
import ssl
import paho.mqtt.client as mqtt
import time
import datetime
import MBus
import Mutiloop_PM
import schedule
import flowMeter

def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        is_connected = True
    else:
        is_connected = False

def on_disconnect(client, userdata, rc):
    global is_connected
    is_connected = False

def MQTT_Connect_sta():
    try:
        global client_sta
        client_sta = mqtt.Client('', True, None, mqtt.MQTTv31)
        client_sta.username_pw_set('infilink_ShangriLa2024TPE', 'wCGTd25n')
        client_sta.tls_set(cert_reqs=ssl.CERT_NONE)
        client_sta.connect('mqtt-device.fetiot3s1.fetnet.net', 8884 , 60)
        client_sta.loop_start()
        time.sleep(1)
        client_sta.on_connect
    except:
        print("error_connect_Sta")

def MQTT_Connect_pro():
    try:
        global client_pro
        client_pro = mqtt.Client('', True, None, mqtt.MQTTv31)
        client_pro.username_pw_set('infilink_ShangriLa2024TPE', '5WufQ879')
        client_pro.tls_set(cert_reqs=ssl.CERT_NONE)
        client_pro.connect('mqtt-device.fetiot3p1.fetnet.net', 8884 , 60)
        client_pro.loop_start()
        time.sleep(1)
        client_pro.on_connect
    except:
        print("error_connect_Pro")

def Connect_Mqtt_Pro():
    try:
        client_pro.connect('mqtt-device.fetiot3p1.fetnet.net', 8884 , 60)
        return 1;
    except:
        return 0;

def Connect_Mqtt_Sta():
    try:
        client_pro.connect('mqtt-device.fetiot3p1.fetnet.net', 8884 , 60)
        return 1;
    except:
        return 0;

def FET_Publish_Product(Meter_data,access_token,timestamp):
    try:
        con_mqtt = Connect_Mqtt_Pro()
        if con_mqtt == 1:
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
    
            data03 = client_pro.publish('/SHANGRILA2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
            time.sleep(5)
            print ("Production= " + data03)
            print ("Production= " + mod_payload)
        else:
            MQTT_Connect_pro()
            time.sleep(5)
    except:
        pass

def FET_Publish_Station(Meter_data,access_token,timestamp):
    try:
        con_mqtt = Connect_Mqtt_Sta()
        if con_mqtt == 1:
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
    
            data03 = client_sta.publish('/SHANGRILA2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
            time.sleep(10)
            print ("Station= " + data03)
            print ("Station= " + mod_payload)
        else:
            MQTT_Connect_sta()
            time.sleep(5)
    except:
        pass

def FlowMeter_Publish_Station(Meter_data,access_token,timestamp):
    try:
        con_mqtt = Connect_Mqtt_Sta()
        if con_mqtt == 1:
            mod_payload = [
                {"access_token":access_token,
                "app":"ShangriLa2024TPE",
                "type":"flow_meter",
                "data":[
                    {"timestemp":timestamp,
                     "values":{
                        "flowmeter_rt_volume_flow_rate":Meter_data[0],
                        "flowmeter_rt_energy_gjhr":Meter_data[1],
                        "flowmeter_rt_energy_rth":Meter_data[2],
                        "flowmeter_rt_flow_rate":Meter_data[3],
                        "flowmeter_total_volume_flow_rate":Meter_data[4],
                        "flowmeter_total_energy_gjhr":Meter_data[5],
                        "flowmeter_total_energy_rth":Meter_data[6],
                        "flowmeter_temperature_inlet":Meter_data[7],
                        "flowmeter_temperature_outlet":Meter_data[8],
                        "alive":1
                        }}]}
                ]
        else:
            MQTT_Connect_sta()
            time.sleep(5)
        data03 = client_sta.publish('/SHANGRILA2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
        time.sleep(10)
        print ("Station= " + data03)
        print ("Station= " + mod_payload)
    except:
        pass

def FlowMeter_Publish_Production(Meter_data,access_token,timestamp):
    try:
        con_mqtt = Connect_Mqtt_Pro()
        if con_mqtt == 1:
            mod_payload = [
                {"access_token":access_token,
                "app":"ShangriLa2024TPE",
                "type":"flow_meter",
                "data":[
                    {"timestemp":timestamp,
                     "values":{
                        "flowmeter_rt_volume_flow_rate":Meter_data[0],
                        "flowmeter_rt_energy_gjhr":Meter_data[1],
                        "flowmeter_rt_energy_rth":Meter_data[2],
                        "flowmeter_rt_flow_rate":Meter_data[3],
                        "flowmeter_total_volume_flow_rate":Meter_data[4],
                        "flowmeter_total_energy_gjhr":Meter_data[5],
                        "flowmeter_total_energy_rth":Meter_data[6],
                        "flowmeter_temperature_inlet":Meter_data[7],
                        "flowmeter_temperature_outlet":Meter_data[8],
                        "alive":1
                        }}]}
                ]   
    
            data03 = client_pro.publish('/SHANGRILA2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
            time.sleep(10)
            print ("Production= " + data03)
            print ("Production= " + mod_payload)
        else:
            MQTT_Connect_pro()
            time.sleep(5)
    except:
        pass

def do_job():
    
    try:
        now = datetime.datetime.now()
        aligned_minute = now.minute - (now.minute % 5)
        aligned_time = now.replace(minute=aligned_minute, second=0, microsecond=0)
        timestamp = int(time.mktime(aligned_time.timetuple()))
        
        
        PowerMeter = MBus.read_3p3w_meter('/dev/ttyS3',30,1)
        FET_Publish_Product(PowerMeter,"4ebb30b3db7546b194334f7a0188b487",timestamp)
        FET_Publish_Station(PowerMeter,"4ebb30b3db7546b194334f7a0188b487",timestamp)
    
        PowerMeter = MBus.read_3p3w_meter('/dev/ttyS3',31,1)
        FET_Publish_Product(PowerMeter,"84f4d26e14bc45ddab170a48b9cc1e10",timestamp)
        FET_Publish_Station(PowerMeter,"84f4d26e14bc45ddab170a48b9cc1e10",timestamp)
    
        PowerMeter = MBus.read_3p3w_meter('/dev/ttyS3',32,1)
        FET_Publish_Product(PowerMeter,"99b270cf07544505a91fe924062af584",timestamp)
        FET_Publish_Station(PowerMeter,"99b270cf07544505a91fe924062af584",timestamp)
    
        PowerMeter = MBus.read_3p3w_meter('/dev/ttyS7',12,1)
        FET_Publish_Product(PowerMeter,"38e20a608eae40f49e2a1f1f6f286fea",timestamp)
        FET_Publish_Station(PowerMeter,"38e20a608eae40f49e2a1f1f6f286fea",timestamp)
        
        #----------------------------------------------17--------------------------------

        #PUMP01  
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,0)
        FET_Publish_Product(MutiPowerMeter,"e7c1671b6d59421996e74eade7e4f704",timestamp)
        FET_Publish_Station(MutiPowerMeter,"e7c1671b6d59421996e74eade7e4f704",timestamp)
        #pump02
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,1)
        FET_Publish_Product(MutiPowerMeter,"068fe7d2b16c477ca3f522815513c7f1",timestamp)
        FET_Publish_Station(MutiPowerMeter,"068fe7d2b16c477ca3f522815513c7f1",timestamp)
        #pump03
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,2)
        FET_Publish_Product(MutiPowerMeter,"64688f1c2fe5453998c6c475eddbe5ac",timestamp)
        FET_Publish_Station(MutiPowerMeter,"64688f1c2fe5453998c6c475eddbe5ac",timestamp)
        #pump04
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,3)
        FET_Publish_Product(MutiPowerMeter,"f0c3a47d3f9942ce9e4f8ad4c3b085b1",timestamp)
        FET_Publish_Station(MutiPowerMeter,"f0c3a47d3f9942ce9e4f8ad4c3b085b1",timestamp)

        #---------------------------------------------18---------------------------------

        #PUMP01  
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,0)
        FET_Publish_Product(MutiPowerMeter,"677b94773d93483aa89aa6e869551499",timestamp)
        FET_Publish_Station(MutiPowerMeter,"677b94773d93483aa89aa6e869551499",timestamp)
        #pump02
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,1)
        FET_Publish_Product(MutiPowerMeter,"a7517dd69de34ff99c1a859e3219afa3",timestamp)
        FET_Publish_Station(MutiPowerMeter,"a7517dd69de34ff99c1a859e3219afa3",timestamp)
        #pump03
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,2)
        FET_Publish_Product(MutiPowerMeter,"30eb8f3a70ab4a259575720ca215d190",timestamp)
        FET_Publish_Station(MutiPowerMeter,"30eb8f3a70ab4a259575720ca215d190",timestamp)
        #pump04
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,3)
        FET_Publish_Product(MutiPowerMeter,"a6b3600b6d004b3bae3966ac065c266e",timestamp)
        FET_Publish_Station(MutiPowerMeter,"a6b3600b6d004b3bae3966ac065c266e",timestamp)
        
        #---------------------------------------------15---------------------------------

        #PUMP01  
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',15,0)
        FET_Publish_Product(MutiPowerMeter,"ad680ae8fd9d4b8b8feaca7f1ebf9808",timestamp)
        FET_Publish_Station(MutiPowerMeter,"ad680ae8fd9d4b8b8feaca7f1ebf9808",timestamp)
        #pump02
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',15,1)
        FET_Publish_Product(MutiPowerMeter,"90682c1eec754930bb95cbce47955f99",timestamp)
        FET_Publish_Station(MutiPowerMeter,"90682c1eec754930bb95cbce47955f99",timestamp)
        #pump03
        MutiPowerMeter = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',15,2)
        FET_Publish_Product(MutiPowerMeter,"e37990074b0e499bbf0e5a3c27e7cccd",timestamp)
        FET_Publish_Station(MutiPowerMeter,"e37990074b0e499bbf0e5a3c27e7cccd",timestamp)
        
        PowerMeter = flowMeter.flow_meter('/dev/ttyS7',22,1)
        FlowMeter_Publish_Station(PowerMeter,"9382460cc8534e368589b0956a859f9f",timestamp)
        FlowMeter_Publish_Production(PowerMeter,"9382460cc8534e368589b0956a859f9f",timestamp)
        
    except:
        pass


#schedule.every(5).minutes.do(do_job)
schedule.every(10).seconds.do(do_job)

if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            pass