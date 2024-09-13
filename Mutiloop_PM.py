import codecs
# -*- coding: UTF-8 -*-

import time
import serial
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import struct


master = modbus_rtu.RtuMaster(serial.Serial(port='/dev/ttyS3', baudrate=9600, bytesize=8, parity="N", stopbits=1, xonxoff=0))
master.set_timeout(5.0)
master.set_verbose(True)

def create_modbus_connection():
    global master
    try:
        master = modbus_rtu.RtuMaster(serial.Serial(port='/dev/ttyS3', baudrate=9600, bytesize=8, parity="N", stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
    except:
        pass

def convert_value(val):
    if 0 <= val <= 32767:
        return val * 0.001
    elif 32768 <= val <= 65535:
        return ((65535-val) * (-0.001))
    else:
        return 1

def conv(num1,num2):
    #check negative
    num1_negative = (num1>>15) & 0x1
    num2_negative = (num2>>15) & 0x1
    
    if num1_negative == 1:
        num1_conv = (0xFFFF - num1)
        num1_conv = num1_conv * (-1)
    else:
        num1_conv = num1
    if num2_negative == 1:
        num2_conv = (0xFFFF - num2)
        num2_conv = num2_conv * (-1)
    else:
        num2_conv = num2
    num = (num2_conv*32768)+num1_conv
    
    return num

def VoltageConv(num1, num2):
    combined_num = (num1 << 16) | num2
    float_num = round(combined_num/10,1)
    return float_num

def CurrntConv(num1, num2):
    combined_num = (num1 << 16) | num2
    float_num = round(combined_num/1000,1)
    return float_num

def kWConv(num1, num2):
    combined_num = (num1 << 16) | num2
    packed_num = struct.pack('i', combined_num)
    
    return packed_num

def Read_MutiPowerMeter(port,ID,cound):
    MainPW_meter = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    try:
        master = modbus_rtu.RtuMaster(serial.Serial(port=port, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        
        PowerVoltage_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, 4105, 8)
        PowerVoltage_V1 = VoltageConv(PowerVoltage_Data[0], PowerVoltage_Data[1])
        PowerVoltage_V2 = VoltageConv(PowerVoltage_Data[2], PowerVoltage_Data[3])
        PowerVoltage_V3 = VoltageConv(PowerVoltage_Data[4], PowerVoltage_Data[5])
        PowerVoltage_Vavg = VoltageConv(PowerVoltage_Data[6], PowerVoltage_Data[7])
        I_Reg_addr = 5120 + 768 * cound
        PowerCurrnet_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, I_Reg_addr, 8)
        PowerCurrnet_I1 = CurrntConv(PowerCurrnet_Data[0], PowerCurrnet_Data[1])
        PowerCurrnet_I2 = CurrntConv(PowerCurrnet_Data[2], PowerCurrnet_Data[3])
        PowerCurrnet_I3 = CurrntConv(PowerCurrnet_Data[4], PowerCurrnet_Data[5])
        PowerCurrnet_Iavg = CurrntConv(PowerCurrnet_Data[6], PowerCurrnet_Data[7])
        PowerFreq_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, 4096, 1)
        PowerFreq_Value = round(PowerFreq_Data[0]*0.01,2)
        kw_Reg_addr = 5128 + 768 * cound
        PowerkW_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, kw_Reg_addr, 8)
        PowerkW_Iavg = conv(PowerkW_Data[7], PowerkW_Data[6])
        kvar_Reg_addr = 5136 + 768 * cound
        PowerkVAR_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, kvar_Reg_addr, 8)
        PowerkVAR_Iavg = conv(PowerkVAR_Data[7], PowerkVAR_Data[6])
        PF_Reg_addr = 5155 + 768 * cound
        PowerFactor_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, PF_Reg_addr, 1)
        PowerFactor = round(convert_value(PowerFactor_Data[0]),2)
        kwh_Reg_addr = 5194 + 768 * cound
        Energykwh_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, kwh_Reg_addr, 2)
        Energykwh = (conv(Energykwh_Data[1], Energykwh_Data[0])*0.1)
        kvah_Reg_addr = 5202 + 768 * cound
        Energykvah_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, kvah_Reg_addr, 2)
        Energykvah = (conv(Energykvah_Data[1], Energykvah_Data[0])*0.1)
        DM_Reg_addr = 5168 + 768 * cound
        demand_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, DM_Reg_addr, 2)
        demand = conv(demand_Data[1], demand_Data[0])
        kvas_Reg_addr = 5144 + 768 * cound
        PowerkVAS_Data = master.execute(ID, cst.READ_HOLDING_REGISTERS, kvas_Reg_addr, 8)
        PowerkVAS_Iavg = conv(PowerkVAS_Data[7], PowerkVAS_Data[6])
        


        
        
        MainPW_meter[0] =  round(PowerFreq_Value,2)
        MainPW_meter[1] =  round(PowerVoltage_V1,2)
        MainPW_meter[2] =  round(PowerVoltage_V2,2)
        MainPW_meter[3] =  round(PowerVoltage_V3,2)
        MainPW_meter[4] =  round(PowerVoltage_Vavg,2)
        MainPW_meter[5] =  round(PowerCurrnet_I1,2)
        MainPW_meter[6] =  round(PowerCurrnet_I2,2)
        MainPW_meter[7] =  round(PowerCurrnet_I3,2)
        MainPW_meter[8] =  round(PowerCurrnet_Iavg,2)
        MainPW_meter[9] =  round(PowerkW_Iavg,2)
        MainPW_meter[10] =  round(PowerkVAR_Iavg,2)
        MainPW_meter[11] =  round(PowerkVAS_Iavg,2)
        MainPW_meter[12] =  round(PowerFactor,2)
        MainPW_meter[13] =  round(demand,2)
        MainPW_meter[14] =  round(Energykwh,2)
        MainPW_meter[15] =  round(Energykvah,2)
        MainPW_meter[16] =  1
       
        return (MainPW_meter)


    except:
        MainPW_meter[0] = 0
        MainPW_meter[1] = 0
        MainPW_meter[2] = 0
        MainPW_meter[3] = 0
        MainPW_meter[4] = 0
        MainPW_meter[5] = 0
        MainPW_meter[6] = 0
        MainPW_meter[7] = 0
        MainPW_meter[8] = 0
        MainPW_meter[9] = 0
        MainPW_meter[10] = 0
        MainPW_meter[11] = 0
        MainPW_meter[12] = 0
        MainPW_meter[13] = 0
        MainPW_meter[14] = 0
        MainPW_meter[15] = 0
        MainPW_meter[16] =  0

        time.sleep(1)
        return (MainPW_meter) 

if __name__ == '__main__':
    print(Read_MutiPowerMeter('/dev/ttyS3',15,0))
    print(Read_MutiPowerMeter('/dev/ttyS3',15,1))
    print(Read_MutiPowerMeter('/dev/ttyS3',15,2))
    print(Read_MutiPowerMeter('/dev/ttyS3',15,3))
    
