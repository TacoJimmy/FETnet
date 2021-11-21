import pwmeter
import time

while True:
    a = pwmeter.read_3p3w_meter('/dev/ttyS1',1,1)
    print(a)
    time.sleep(5)
    