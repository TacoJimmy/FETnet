
# -*- coding: utf-8 -*-

import time
import serial
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import struct


SERIAL_PORT = 'COM6'  
BAUDRATE = 9600             
PARITY = 'N'                
STOPBITS = 1                
BYTESIZE = 8

def float_num(int16_1, int16_2):
    combined = (int16_2 << 16) | int16_1
    byte_data = struct.pack('<I', combined)
    float_value = struct.unpack('<f', byte_data)[0]

    return (float_value)


def flow_meter(PORT,ID,loop):
    loop = loop - 1
    flow_meter = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    try:
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        
        FlowMeter1 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 0, 2)
        RT_Flowdata = round(float_num(FlowMeter1[0], FlowMeter1[1]),2)
        FlowMeter2 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 2, 2)
        RT_Energydata = round(float_num(FlowMeter2[0], FlowMeter2[1]),2)
        FlowMeter3 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 4, 2)
        RT_FlowSpeeddata = round(float_num(FlowMeter3[0], FlowMeter3[1]),2)
        FlowMeter4 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 6, 2)
        RT_FlowSpeeddata = round(float_num(FlowMeter4[0], FlowMeter4[1]),2)
        FlowMeter5 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 8, 2)
        RT_FlowSpeeddata = round(float_num(FlowMeter5[0], FlowMeter5[1]),2)
        FlowMeter6 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 10, 2)
        RT_FlowSpeeddata = round(float_num(FlowMeter6[0], FlowMeter6[1]),2)
        FlowMeter7 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 12, 2)
        RT_FlowSpeeddata = round(float_num(FlowMeter7[0], FlowMeter7[1]),2)
        
        
        #RT_Flow = master.execute(ID, cst.READ_HOLDING_REGISTERS, 34, 2)
        #RT_Flowdata = round(float_num(RT_Flow[0], RT_Flow[1]),2)
        
        
        Temp1 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 32, 2)
        Temp11 = round(float_num(Temp1[0], Temp1[1]),2)
        Temp2 = master.execute(ID, cst.READ_HOLDING_REGISTERS, 34, 2)
        Temp21 = round(float_num(Temp2[0], Temp2[1]),2)
        
        
        
        return (RT_Flowdata,RT_Energydata,RT_FlowSpeeddata,Temp11,Temp21)
        #return (RT_Flowdata,RT_Energydata,RT_FlowSpeeddata,Temp11,Temp21)

    except:
        pass


if __name__ == '__main__':
    print(flow_meter('COM6',22,1))