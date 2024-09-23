
# -*- coding: utf-8 -*-

import time
import serial
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import struct



def float_num(int16_1, int16_2):
    combined = (int16_2 << 16) | int16_1
    byte_data = struct.pack('<I', combined)
    float_value = struct.unpack('<f', byte_data)[0]
    return (float_value)


def read_3p3w_meter(PORT,ID,loop):
    loop = loop - 1
    MainPW_meter = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    try:
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        pw_frq = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28672, 2)
        pw_v_u = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28674, 8)
        #pw_v_u = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28682, 6)
        pw_i_l = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28690, 8)
        pw_power_w = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28706, 2)
        pw_power_var = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28714, 2)
        pw_power_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28722, 2)
        pw_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28730, 2)
        pw_dm_w = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28738, 2)
        pw_consum_kwh = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28768, 2)
        pw_consum_kvarh = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28776, 2)
        
        
        MainPW_meter[0] =  round(float_num(pw_frq[1], pw_frq[0]),2)
        MainPW_meter[1] =  round(float_num(pw_v_u[1], pw_v_u[0]),2)
        MainPW_meter[2] =  round(float_num(pw_v_u[3], pw_v_u[2]),2)
        MainPW_meter[3] =  round(float_num(pw_v_u[5], pw_v_u[4]),2)
        MainPW_meter[4] =  round(float_num(pw_v_u[7], pw_v_u[6]),2)
        MainPW_meter[5] =  round(float_num(pw_i_l[1], pw_i_l[0]),2)
        MainPW_meter[6] =  round(float_num(pw_i_l[3], pw_i_l[2]),2)
        MainPW_meter[7] =  round(float_num(pw_i_l[5], pw_i_l[4]),2)
        MainPW_meter[8] =  round(float_num(pw_i_l[7], pw_i_l[6]),2)
        MainPW_meter[9] =  round(float_num(pw_power_w[1], pw_power_w[0])*0.001,2)
        MainPW_meter[10] =  round(float_num(pw_power_var[1], pw_power_var[0])*0.001,2)
        MainPW_meter[11] =  round(float_num(pw_power_va[1], pw_power_va[0])*0.001,2)
        MainPW_meter[12] =  round(float_num(pw_pf[1], pw_pf[0]),2)
        MainPW_meter[13] =  round(float_num(pw_dm_w[1], pw_dm_w[0]),2)
        MainPW_meter[14] =  round(float_num(pw_consum_kwh[1], pw_consum_kwh[0]),2)
        MainPW_meter[15] =  round(float_num(pw_consum_kvarh[1], pw_consum_kvarh[0]),2)
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

def read_PowerMeter(PORT,ID,loop):
    loop = loop - 1
    MainPW_meter = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
    master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
    master.set_timeout(5.0)
    master.set_verbose(True)
    pw_frq = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28672, 2)
    pw_v_u = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28682, 8)
    #pw_v_u = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28682, 6)
    pw_i_l = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28690, 8)
    pw_power_w = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28706, 2)
    pw_power_var = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28714, 2)
    pw_power_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28722, 2)
    pw_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28730, 2)
    pw_dm_w = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28738, 2)
    pw_consum_kwh = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28768, 2)
    pw_consum_kvarh = master.execute(ID, cst.READ_HOLDING_REGISTERS, 28776, 2)
        
        
    MainPW_meter[0] =  round(float_num(pw_frq[1], pw_frq[0]),2)
    MainPW_meter[1] =  round(float_num(pw_v_u[1], pw_v_u[0]),2)
    MainPW_meter[2] =  round(float_num(pw_v_u[3], pw_v_u[2]),2)
    MainPW_meter[3] =  round(float_num(pw_v_u[5], pw_v_u[4]),2)
    MainPW_meter[4] =  round(float_num(pw_v_u[7], pw_v_u[6]),2)
    MainPW_meter[5] =  round(float_num(pw_i_l[1], pw_i_l[0]),2)
    MainPW_meter[6] =  round(float_num(pw_i_l[3], pw_i_l[2]),2)
    MainPW_meter[7] =  round(float_num(pw_i_l[5], pw_i_l[4]),2)
    MainPW_meter[8] =  round(float_num(pw_i_l[7], pw_i_l[6]),2)
    MainPW_meter[9] =  round(float_num(pw_power_w[1], pw_power_w[0])*0.001,2)
    MainPW_meter[10] =  round(float_num(pw_power_var[1], pw_power_var[0])*0.001,2)
    MainPW_meter[11] =  round(float_num(pw_power_va[1], pw_power_va[0])*0.001,2)
    MainPW_meter[12] =  round(float_num(pw_pf[1], pw_pf[0]),2)
    MainPW_meter[13] =  round(float_num(pw_dm_w[1], pw_dm_w[0]),2)
    MainPW_meter[14] =  round(float_num(pw_consum_kwh[1], pw_consum_kwh[0]),2)
    MainPW_meter[15] =  round(float_num(pw_consum_kvarh[1], pw_consum_kvarh[0]),2)
    MainPW_meter[16] =  1
      
    return (MainPW_meter)
    
if __name__ == '__main__':
    while True:
        print(read_PowerMeter('/dev/ttyS7',12,1))
        time.sleep(5)
        print(read_PowerMeter('/dev/ttyS3',30,1))
        time.sleep(5)