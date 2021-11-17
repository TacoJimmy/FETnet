
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

'''
def read_mainpw_meter(PORT,ID):
    
    try:
        MainPW_meter = [0,0,0,0,0,0,0]
        
        #PORT = 'COM6'
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        pw_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 3, 3)
        pw_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, 10, 1)
        pw_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 19, 1)
        pw_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, 39, 2)
        
        MainPW_meter[0] =  pw_va[0] * 0.1
        MainPW_meter[1] =  pw_va[1] * 0.01
        MainPW_meter[2] =  pw_va[2] * 0.01
        MainPW_meter[3] =  MainPW_meter[1] - MainPW_meter[2] # L1-L2
        MainPW_meter[4] =  pw_power[0] * 0.1    
        
        MainPW_meter[5] =  pw_pf[0] 
        MainPW_meter[6] =  pw_consum[1] + pw_consum[0] * 65535 
        return (MainPW_meter)
        
        master.close()
    except:
        master.close()
        #print('loss_connect')
        return ('loss_connect')
'''
def neg_num(numb): 
    ret_numb = 0
    if numb >> 15 == 1:
        ret_numb = (65536 - numb)*-1
    else:
        ret_numb = numb
    return ret_numb
        


def read_ACpw_meter01(PORT,ID): # 1p2w power meter
    try:
        AC01_meter = [0,0,0,0,0,0]
        i_pf = 0
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        AC_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 1, 1)
        AC_cur = master.execute(ID, cst.READ_HOLDING_REGISTERS, 2, 1)
        AC_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, 7, 1)
        AC_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 10, 1)
        AC_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, 39, 2)
        
        
        
        AC01_meter[0] = (AC_va[0]*0.1)
        AC01_meter[1] = AC_cur[0]*0.01
        AC01_meter[2] = neg_num(AC_power[0])*0.01
        AC01_meter[3] = neg_num(AC_pf[0])*0.001
        AC01_meter[4] = (AC_consum[1] + AC_consum[0]*65536)*0.1
        AC01_meter[5] = 1
        return (AC01_meter)
        master.close()
    except:
        master.close()
        AC01_meter[0] = 0
        AC01_meter[1] = 0
        AC01_meter[2] = 0
        AC01_meter[3] = 0
        AC01_meter[4] = 0
        AC01_meter[5] = 0
        return (AC01_meter)

    
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
 

def read_1p2w_meter(PORT,ID,loop): # 1p2w power meter
    
    loop = loop - 1
    
    try:
        AC01_meter = [0,0,0,0,0,0]
        
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        
        AC_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 1, 1)
        AC_cur = master.execute(ID, cst.READ_HOLDING_REGISTERS, (2+loop), 1)
        AC_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, (7+loop*4), 1)
        AC_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, (10+loop*4), 1)
        AC_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, (39+loop*4), 2)
        
        AC01_meter[0] = (AC_va[0]*0.1)
        AC01_meter[1] = AC_cur[0]*0.01
        AC01_meter[2] = neg_num(AC_power[0])*0.01
        AC01_meter[3] = neg_num(AC_pf[0])*0.001
        AC01_meter[4] = (AC_consum[1] + AC_consum[0]*65536)*0.1
        AC01_meter[5] = 1
        master.close()
        # return ('{:.2f},{:.2f},{:.2f},{:.2f},{:.1f}'.format(*AC01_meter))
        return (AC01_meter)
    except:
        master.close()
        AC01_meter[0] = 0
        AC01_meter[1] = 0
        AC01_meter[2] = 0
        AC01_meter[3] = 0
        AC01_meter[4] = 0
        AC01_meter[5] = 0
        return (AC01_meter)

'''  
def read_ACpw_meter02(PORT,ID):
    
    try:
        AC02_meter = [0,0,0,0,0];
        
        #PORT = 'COM10'
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        AC_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 1, 1)
        AC_cur = master.execute(ID, cst.READ_HOLDING_REGISTERS, 3, 1)
        AC_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, 7, 1)
        AC_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 10, 1)
        AC_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, 41, 2)
            
        AC02_meter[0] = AC_va[0]*0.1
        AC02_meter[1] = AC_cur[0]*0.01
        AC02_meter[2] = AC_power[0]*0.01
        AC02_meter[3] = AC_pf[0]
        AC02_meter[4] = AC_consum[1] + AC_consum[0]*65536
        
        return (AC02_meter)
        master.close()
    except:
        master.close()
        return ('loss_connect')
    
def read_ACpw_meter03(PORT,ID):
    
    try:
        AC03_meter = [0,0,0,0,0];
        
        #PORT = 'COM6'
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        AC_va = master.execute(ID, cst.READ_HOLDING_REGISTERS, 1, 1)
        AC_cur = master.execute(ID, cst.READ_HOLDING_REGISTERS, 3, 1)
        AC_power = master.execute(ID, cst.READ_HOLDING_REGISTERS, 7, 1)
        AC_pf = master.execute(ID, cst.READ_HOLDING_REGISTERS, 10, 1)
        AC_consum = master.execute(ID, cst.READ_HOLDING_REGISTERS, 39, 2)
        
             
        AC03_meter[0] = AC_va[0]*0.1
        AC03_meter[1] = AC_cur[0]*0.01
        AC03_meter[2] = AC_power[0]*0.01
        AC03_meter[3] = AC_pf[0]
        AC03_meter[4] = AC_consum[1] + AC_consum[0]*65536
        
        #print(AC01_vol, AC01_cur, AC01_power, AC01_pf, AC01_consum)
        return (AC03_meter)
        master.close()
    except:
        master.close()
        #print('loss_connect')
        return ('loss_connect')

'''
'''    
while True:

   
    # 3相電，
    a = read_3p3w_meter('COM3',1,1) # prot =ComPort, ID = device address , loop(1or2)
    b = read_3p3w_meter('COM3',1,2) # prot =ComPort, ID = device address , loop(1or2)
    print("Loop1 data",a)
    print(type(a))
    print("Loop2 data",b)
    print(type(b))
    time.sleep(5)
   
  
    

    a = read_1p3w_meter('COM3',1,1) # prot =ComPort, ID = device address , loop(1or2)
    b = read_1p3w_meter('COM3',1,2) # prot =ComPort, ID = device address , loop(1or2)
    print("Loop1 data",a)
    print("Loop1 data",b)
    
    a = read_1p2w_meter('COM3',1,1) # prot =ComPort, ID = device address , loop
    b = read_1p2w_meter('COM3',1,2) # prot =ComPort, ID = device address , loop
    c = read_1p2w_meter('COM3',1,3) # prot =ComPort, ID = device address , loop
    d = read_1p2w_meter('COM3',1,4) # prot =ComPort, ID = device address , loop
    
    # print(a)
    print("Loop1 data",a)
    print("Loop2 data",b)
    print("Loop3 data",c)
    print("Loop4 data",d)
'''    
    

