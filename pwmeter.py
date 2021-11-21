
# -*- coding: utf-8 -*-

import sys
import time
import serial
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import struct
from _ast import If
import codecs
#from dask.array.random import power
import statistics


def neg_num(numb): 
    ret_numb = 0
    if numb >> 15 == 1:
        ret_numb = (65536 - numb)*-1
    else:
        ret_numb = numb
    return ret_numb
        


def read_3p3w_meter(PORT,ID,loop):
    loop = loop - 1
    MainPW_meter = [0,0,0,0,0,0,0,0]
    try:
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        pw_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 4, 1)
        pw_cur = master.execute(ID, cst.READ_HOLDING_REGISTERS, 5+loop*4, 3)
        pw_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, 15+loop*10, 1)
        pw_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 24+loop*12, 1)
        pw_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, 39+loop*4, 2)
        
        MainPW_meter[0] =  pw_va[0] * 0.1
        MainPW_meter[1] =  pw_cur[0] * 0.01
        MainPW_meter[2] =  pw_cur[1] * 0.01
        MainPW_meter[3] =  pw_cur[2] * 0.01
        MainPW_meter[4] =  neg_num(pw_power[0]) * 0.01 
        MainPW_meter[5] =  neg_num(pw_pf[0])*0.001
        MainPW_meter[6] =  (pw_consum[1] + pw_consum[0] * 65535)*0.1
        MainPW_meter[7] = 1 
        master.close()
        time.sleep(1)
        # return ('{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}'.format(*MainPW_meter))
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
        master.close()
        return (MainPW_meter) 
    else:
        MainPW_meter[0] = 0
        MainPW_meter[1] = 0
        MainPW_meter[2] = 0
        MainPW_meter[3] = 0
        MainPW_meter[4] = 0
        MainPW_meter[5] = 0
        MainPW_meter[6] = 0
        MainPW_meter[7] = 0
        master.close()
        return (MainPW_meter) 
    
def read_1p3w_meter(PORT,ID,loop):
    loop = loop - 1
    try:
        MainPW_meter = [0,0,0,0,0,0,0,0]
        
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        pw_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 3, 1)
        pw_cur = master.execute(ID, cst.READ_HOLDING_REGISTERS, 4+loop*2, 2)
        pw_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, 10+loop*12, 1)
        pw_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 19+loop*12, 1)
        pw_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, 39+loop*4, 2)
        
        MainPW_meter[0] =  pw_va[0] * 0.1
        MainPW_meter[1] =  pw_cur[0] * 0.01
        MainPW_meter[2] =  pw_cur[1] * 0.01
        MainPW_meter[3] =  MainPW_meter[1] - MainPW_meter[2] # L1-L2
        MainPW_meter[4] =  neg_num(pw_power[0]) * 0.01    
        MainPW_meter[5] =  neg_num(pw_pf[0])*0.001
        MainPW_meter[6] =  (pw_consum[1] + pw_consum[0] * 65535)*0.1
        MainPW_meter[7] =  1
        master.close()
        time.sleep(1)
        # return ('{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}'.format(*MainPW_meter))
        return (MainPW_meter)
    except:
        master.close()
        MainPW_meter[0] =  0
        MainPW_meter[1] =  0
        MainPW_meter[2] =  0
        MainPW_meter[3] =  0
        MainPW_meter[4] =  0
        MainPW_meter[5] =  0
        MainPW_meter[6] =  0
        MainPW_meter[7] =  0
        return (MainPW_meter)
    
    else:
        MainPW_meter[0] = 0
        MainPW_meter[1] = 0
        MainPW_meter[2] = 0
        MainPW_meter[3] = 0
        MainPW_meter[4] = 0
        MainPW_meter[5] = 0
        MainPW_meter[6] = 0
        MainPW_meter[7] = 0
        master.close()
        return (MainPW_meter)
 

def read_1p2w_meter(PORT,ID,loop): # 1p2w power meter
    
    loop = loop - 1
    
    try:
        AC_meter = [0,0,0,0,0,0]
        
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        
        AC_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 1, 1)
        AC_cur = master.execute(ID, cst.READ_HOLDING_REGISTERS, (2+loop), 1)
        AC_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, (7+loop*4), 1)
        AC_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, (10+loop*4), 1)
        AC_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, (39+loop*4), 2)
        
        AC_meter[0] = (AC_va[0]*0.1)
        AC_meter[1] = AC_cur[0]*0.01
        AC_meter[2] = neg_num(AC_power[0])*0.01
        AC_meter[3] = neg_num(AC_pf[0])*0.001
        AC_meter[4] = (AC_consum[1] + AC_consum[0]*65536)*0.1
        AC_meter[5] = 1
        master.close()
        time.sleep(1)
        # return ('{:.2f},{:.2f},{:.2f},{:.2f},{:.1f}'.format(*AC_meter))
        return (AC_meter)
    except:
        master.close()
        AC_meter[0] = 0
        AC_meter[1] = 0
        AC_meter[2] = 0
        AC_meter[3] = 0
        AC_meter[4] = 0
        AC_meter[5] = 0
        return (AC_meter) 
    
    else:
        AC_meter[0] = 0
        AC_meter[1] = 0
        AC_meter[2] = 0
        AC_meter[3] = 0
        AC_meter[4] = 0
        AC_meter[5] = 0
        AC_meter[6] = 0
        AC_meter[7] = 0
        master.close()
        return (AC_meter)

