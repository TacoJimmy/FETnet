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
from datetime import datetime

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
        time.sleep(2)
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
        time.sleep(2)
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
        time.sleep(2)
        
    except:
        pass

def FET_Publish_Station(Meter_data,access_token,timestamp):
    try:
        
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
        time.sleep(2)
        #print ("Station= " + data03)
        #print ("Station= " + mod_payload)
        
    except:
        pass

def FlowMeter_Publish_Station(Meter_data,access_token,timestamp):
    try:
        
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
        
        data03 = client_sta.publish('/SHANGRILA2024TPE/v1/telemetry/infilink',json.dumps(mod_payload))
        time.sleep(2)
        #print ("Station= " + data03)
        #print ("Station= " + mod_payload)
    except:
        pass

def FlowMeter_Publish_Production(Meter_data,access_token,timestamp):
    try:
        
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
        time.sleep(2)
        #print ("Production= " + data03)
        #print ("Production= " + mod_payload)
        
    except:
        pass

def do_job():
    
    try:
        now = datetime.now()
        aligned_minute = now.minute - (now.minute % 5)
        aligned_time = now.replace(minute=aligned_minute, second=0, microsecond=0)
        timestamp = int(time.mktime(aligned_time.timetuple()))
        PowerMeter0 = MBus.read_3p3w_meter('/dev/ttyS3',30,1)
        
        
            
        PowerMeter1 = MBus.read_3p3w_meter('/dev/ttyS3',31,1)
        PowerMeter2 = MBus.read_3p3w_meter('/dev/ttyS3',32,1)
        PowerMeter3_1 = MBus.read_3p3w_meter('/dev/ttyS7',11,1)
        PowerMeter3_2 = MBus.read_3p3w_meter('/dev/ttyS7',12,1)
        MutiPowerMeter4 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,0)
        MutiPowerMeter5 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,1)
        MutiPowerMeter6 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,2)
        MutiPowerMeter7 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',17,3)
        MutiPowerMeter8 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,0)
        MutiPowerMeter9 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,1)
        MutiPowerMeter10 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,2)
        MutiPowerMeter11 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',18,3)
        MutiPowerMeter12 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',15,0)
        MutiPowerMeter13 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',15,1)
        MutiPowerMeter14 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',15,2)
        MutiPowerMeter16 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS7',15,3)
        MutiPowerMeter17 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS3',16,1)
        MutiPowerMeter18 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS3',16,2)
        MutiPowerMeter19 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS3',16,3)
        MutiPowerMeter20 = Mutiloop_PM.Read_MutiPowerMeter('/dev/ttyS3',16,4)
        PowerMeter15 = flowMeter.flow_meter('/dev/ttyS7',22,1)


        con_mqtt = Connect_Mqtt_Pro()
        if con_mqtt == 1:
            FET_Publish_Product(PowerMeter0,"4ebb30b3db7546b194334f7a0188b487",timestamp)
            FET_Publish_Product(PowerMeter1,"84f4d26e14bc45ddab170a48b9cc1e10",timestamp)
            FET_Publish_Product(PowerMeter2,"99b270cf07544505a91fe924062af584",timestamp)
            FET_Publish_Product(PowerMeter3_1,"38e20a608eae40f49e2a1f1f6f286fea",timestamp)
            FET_Publish_Product(PowerMeter3_2,"94a3713451234f76b8afccb3d574ab7b",timestamp)
            FET_Publish_Product(MutiPowerMeter4,"e7c1671b6d59421996e74eade7e4f704",timestamp)
            FET_Publish_Product(MutiPowerMeter5,"068fe7d2b16c477ca3f522815513c7f1",timestamp)
            FET_Publish_Product(MutiPowerMeter6,"64688f1c2fe5453998c6c475eddbe5ac",timestamp)
            FET_Publish_Product(MutiPowerMeter7,"f0c3a47d3f9942ce9e4f8ad4c3b085b1",timestamp)
            FET_Publish_Product(MutiPowerMeter8,"677b94773d93483aa89aa6e869551499",timestamp)
            FET_Publish_Product(MutiPowerMeter9,"a7517dd69de34ff99c1a859e3219afa3",timestamp)
            FET_Publish_Product(MutiPowerMeter10,"30eb8f3a70ab4a259575720ca215d190",timestamp)
            FET_Publish_Product(MutiPowerMeter11,"a6b3600b6d004b3bae3966ac065c266e",timestamp)
            FET_Publish_Product(MutiPowerMeter12,"ad680ae8fd9d4b8b8feaca7f1ebf9808",timestamp)
            FET_Publish_Product(MutiPowerMeter13,"90682c1eec754930bb95cbce47955f99",timestamp)
            FET_Publish_Product(MutiPowerMeter14,"e37990074b0e499bbf0e5a3c27e7cccd",timestamp)
            FlowMeter_Publish_Station(PowerMeter15,"9382460cc8534e368589b0956a859f9f",timestamp)
            FET_Publish_Product(MutiPowerMeter16,"44820cc117d947749740770e9a86552d",timestamp)
            FET_Publish_Product(MutiPowerMeter17,"a0fb2c02a429442094f3a87756ef9c63",timestamp)
            FET_Publish_Product(MutiPowerMeter18,"5340e7907e1c4fca8be7aaf310bbb0a7",timestamp)
            FET_Publish_Product(MutiPowerMeter19,"e9cd43d872914e908e70fc8d664926bb",timestamp)
            FET_Publish_Product(MutiPowerMeter20,"ce9a9053ba1543c2b734ebba2d03d9c9",timestamp)
        else:
            MQTT_Connect_pro()
            time.sleep(2)


        
        con_mqtt = Connect_Mqtt_Sta()
        if con_mqtt == 1:
            FET_Publish_Station(PowerMeter0,"4ebb30b3db7546b194334f7a0188b487",timestamp)
            FET_Publish_Station(PowerMeter1,"84f4d26e14bc45ddab170a48b9cc1e10",timestamp)
            FET_Publish_Station(PowerMeter2,"99b270cf07544505a91fe924062af584",timestamp)
            FET_Publish_Station(PowerMeter3_1,"38e20a608eae40f49e2a1f1f6f286fea",timestamp)
            FET_Publish_Station(PowerMeter3_2,"94a3713451234f76b8afccb3d574ab7b",timestamp)
            FET_Publish_Station(MutiPowerMeter4,"e7c1671b6d59421996e74eade7e4f704",timestamp)
            FET_Publish_Station(MutiPowerMeter5,"068fe7d2b16c477ca3f522815513c7f1",timestamp)
            FET_Publish_Station(MutiPowerMeter6,"64688f1c2fe5453998c6c475eddbe5ac",timestamp)
            FET_Publish_Station(MutiPowerMeter7,"f0c3a47d3f9942ce9e4f8ad4c3b085b1",timestamp)
            FET_Publish_Station(MutiPowerMeter8,"677b94773d93483aa89aa6e869551499",timestamp)
            FET_Publish_Station(MutiPowerMeter9,"a7517dd69de34ff99c1a859e3219afa3",timestamp)
            FET_Publish_Station(MutiPowerMeter10,"30eb8f3a70ab4a259575720ca215d190",timestamp)
            FET_Publish_Station(MutiPowerMeter11,"a6b3600b6d004b3bae3966ac065c266e",timestamp)
            FET_Publish_Station(MutiPowerMeter12,"ad680ae8fd9d4b8b8feaca7f1ebf9808",timestamp)
            FET_Publish_Station(MutiPowerMeter13,"90682c1eec754930bb95cbce47955f99",timestamp)
            FET_Publish_Station(MutiPowerMeter14,"e37990074b0e499bbf0e5a3c27e7cccd",timestamp)
            FlowMeter_Publish_Production(PowerMeter15,"9382460cc8534e368589b0956a859f9f",timestamp)
            FET_Publish_Station(MutiPowerMeter16,"44820cc117d947749740770e9a86552d",timestamp)
            FET_Publish_Station(MutiPowerMeter17,"a0fb2c02a429442094f3a87756ef9c63",timestamp)
            FET_Publish_Station(MutiPowerMeter18,"5340e7907e1c4fca8be7aaf310bbb0a7",timestamp)
            FET_Publish_Station(MutiPowerMeter19,"e9cd43d872914e908e70fc8d664926bb",timestamp)
            FET_Publish_Station(MutiPowerMeter20,"ce9a9053ba1543c2b734ebba2d03d9c9",timestamp)
        else:
            MQTT_Connect_sta()
            time.sleep(2)
    except:
        pass

MQTT_Connect_pro()
MQTT_Connect_sta()

schedule.every(5).minutes.do(do_job)
#schedule.every(10).seconds.do(do_job)

if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            pass