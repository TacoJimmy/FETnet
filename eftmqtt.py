import pwmeter
import time
import ACCtrl

while True:
    a0 = pwmeter.read_3p3w_meter('/dev/ttyS1',1,1)
    a1 = pwmeter.read_1p2w_meter('/dev/ttyS1',2,1)
    a2 = pwmeter.read_1p2w_meter('/dev/ttyS1',3,1)
    a3 = pwmeter.read_1p2w_meter('/dev/ttyS1',4,1)
    
    b1 = print(ACCtrl.AC_ReadFullFunction('/dev/ttyS4',1))
    b2 = print(ACCtrl.AC_ReadFullFunction('/dev/ttyS4',1))
    b3 = print(ACCtrl.AC_ReadFullFunction('/dev/ttyS4',1))
    print(a0)
    print(a1)
    print(a2)
    print(a3)
    print(b1)
    print(b2)
    print(b3)
    time.sleep(5)
