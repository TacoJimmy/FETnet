# coding:utf-8
import os, io
import codecs
import flask
from flask import render_template
import time
import PW_meter
import AC_ctrl
import FET
from flask_script import Manager
from livereload import Server
from flask_apscheduler import APScheduler
import threading

'''
Created on 2021/11/14
@author: TacoJimmy
'''
a = [0,0,0,0,0,0,0]

app = flask.Flask(__name__)
manager = Manager(app)

class Config(object):
    JOBS = [
        {
            'id': 'read_infor',
            'func': '__main__:read_infor',
            'args': (4, 5),
            'trigger': 'interval',
            'minutes': 1
        },
        {
            'id': 'job1',
            'func': '__main__:job1',
            'args': (1, 2),
            'trigger': 'interval',
            'seconds': 5
        }
    ]

def read_infor(a, b): # send data to cloud
    FET.connect_storemeter('2419-STOREM-F85F74E9')
    FET.connect_AC01Meter('2419-ACMtr1-3C45218B')
    FET.connect_AC01Meter('2419-ACMtr2-536A8D04')
    FET.connect_AC01Meter('2419-ACMtr3-D8E39C46')
    FET.connect_ACstatus('2419-ACInf1-70C552F7')
    FET.connect_ACstatus('2419-ACInf2-6F64A317')
    FET.connect_ACstatus('2419-ACInf3-E4E94775')


def job1(a, b):
    print(str(a) + ' ' + str(b))

def job2(a):
    while True:
        print(a)
        time.sleep(2)
        
        
def job3(a):
    while True:
        print(a)
        time.sleep(3)

@app.route('/home')
@app.route('/')
def home():
    '''
    appInfo = {  # dict
        'LineVolt':'{:.2f}'.format(10),
        'L1Current':'{:.2f}'.format(10),
        'L2Current':'{:.2f}'.format(10),
        'L3Current':'{:.2f}'.format(10),
        'PF':'{:.2f}'.format(10),
        'Power':'{:.2f}'.format(10),
        'Consumption':'{:.2f}'.format(10),
        'alive':1
        }
    return render_template('home.html', appInfo=appInfo)
    '''
    
    #Main_PW = [0,0,0,0,0,0,0,0]
    Main_PW = PW_meter.read_3p3w_meter('COM3',1,1)
    print(Main_PW)
    appInfo = {  # dict
        'LineVolt':'{:.2f}'.format(Main_PW[0]),
        'L1Current':'{:.2f}'.format(Main_PW[1]),
        'L2Current':'{:.2f}'.format(Main_PW[2]),
        'L3Current':'{:.2f}'.format(Main_PW[3]),
        'PF':'{:.2f}'.format(Main_PW[4]),
        'Power':'{:.2f}'.format(Main_PW[5]),
        'Consumption':'{:.2f}'.format(Main_PW[6]),
        'alive':Main_PW[7]
        }
    return render_template('home.html', appInfo=appInfo)
    '''
    a = PW_meter.read_3p3w_meter('COM3',1,1)
    appInfo = {  # dict
        'LineVolt':'{:.2f}'.format(a[0]),
        'L1Current':'{:.2f}'.format(a[1]),
        'L2Current':'{:.2f}'.format(a[2]),
        'L3Current':'{:.2f}'.format(a[3]),
        'PF':'{:.2f}'.format(a[4]),
        'Power':'{:.2f}'.format(a[5]),
        'Consumption':'{:.2f}'.format(a[6]),
        'alive':"1"
    }
    return render_template('home.html', appInfo=appInfo)
    '''
@app.route('/ac01data')
def ac01data():
    ac01_meter = PW_meter.read_1p2w_meter('COM3',1,1)
    ac01_infor = AC_ctrl.AC_ctrl.AC_ReadFullFunction('COM3',1)
    appInfo = {  # dict
        'AC01voltage':'{:.2f}'.format(ac01_meter[0]),
        'AC01current':'{:.2f}'.format(ac01_meter[1]),
        'AC01pf':'{:.2f}'.format(ac01_meter[2]),
        'AC01power':'{:.2f}'.format(ac01_meter[3]),
        'AC01consumption':'{:.2f}'.format(ac01_meter[4]),
        'AC01alive':'{:.2f}'.format(ac01_meter[5]),
        'AC01status':'{:.2f}'.format(ac01_infor[0]),
        'AC01mode':'{:.2f}'.format(ac01_infor[1]),
        'AC01settemp':'{:.2f}'.format(ac01_infor[2]),
        'AC01windspeed':'{:.2f}'.format(ac01_infor[3]),
        'AC01roomtemp':'{:.2f}'.format(ac01_infor[4]),
        'AC01alive':'{:.2f}'.format(ac01_infor[5]),        
    }
    return render_template('ac01data.html', appInfo=appInfo)
    
@app.route('/ac02data')
def ac02data():
    ac02_meter = PW_meter.read_1p2w_meter('COM3',2,1)
    ac02_infor = AC_ctrl.AC_ctrl.AC_ReadFullFunction('COM3',2)
    appInfo = {  # dict
        'AC01voltage':'{:.2f}'.format(ac02_meter[0]),
        'AC01current':'{:.2f}'.format(ac02_meter[1]),
        'AC01pf':'{:.2f}'.format(ac02_meter[2]),
        'AC01power':'{:.2f}'.format(ac02_meter[3]),
        'AC01consumption':'{:.2f}'.format(ac02_meter[4]),
        'AC01alive':'{:.2f}'.format(ac02_meter[5]),
        'AC01status':'{:.2f}'.format(ac02_infor[0]),
        'AC01mode':'{:.2f}'.format(ac02_infor[1]),
        'AC01settemp':'{:.2f}'.format(ac02_infor[2]),
        'AC01windspeed':'{:.2f}'.format(ac02_infor[3]),
        'AC01roomtemp':'{:.2f}'.format(ac02_infor[4]),
        'AC01alive':'{:.2f}'.format(ac02_infor[5]),        
    }
    return render_template('ac02data.html', appInfo=appInfo)

@app.route('/ac03data')
def ac03data():
    ac03_meter = PW_meter.read_1p2w_meter('COM3',3,1)
    ac03_infor = AC_ctrl.AC_ctrl.AC_ReadFullFunction('COM3',3)
    appInfo = {  # dict
        'AC01voltage':'{:.2f}'.format(ac03_meter[0]),
        'AC01current':'{:.2f}'.format(ac03_meter[1]),
        'AC01pf':'{:.2f}'.format(ac03_meter[2]),
        'AC01power':'{:.2f}'.format(ac03_meter[3]),
        'AC01consumption':'{:.2f}'.format(ac03_meter[4]),
        'AC01alive':'{:.2f}'.format(ac03_meter[5]),
        'AC01status':'{:.2f}'.format(ac03_infor[0]),
        'AC01mode':'{:.2f}'.format(ac03_infor[1]),
        'AC01settemp':'{:.2f}'.format(ac03_infor[2]),
        'AC01windspeed':'{:.2f}'.format(ac03_infor[3]),
        'AC01roomtemp':'{:.2f}'.format(ac03_infor[4]),
        'AC01alive':'{:.2f}'.format(ac03_infor[5]),        
    }
    return render_template('ac03data.html', appInfo=appInfo)
'''
@app.route('/ac04data')
def ac04data():
        # a = PW_meter.read_3p3w_meter('COM3',1,1)
        appInfo = {  # dict
            'AC04voltage':'{:.2f}'.format(10.00),
            'AC04current':'{:.2f}'.format(11.00),
            'AC04pf':'{:.2f}'.format(12.00),
            'AC04power':'{:.2f}'.format(13.00),
            'AC04consumption':'{:.2f}'.format(14.00),
            'AC04alive':'{:.2f}'.format(15.00),
            'AC04status':'{:.2f}'.format(10.00),
            'AC04mode':'{:.2f}'.format(11.00),
            'AC04settemp':'{:.2f}'.format(12.00),
            'AC04windspeed':'{:.2f}'.format(13.00),
            'AC04roomtemp':'{:.2f}'.format(14.00),
            'AC04alive':'{:.2f}'.format(15.00),        
        }
        return render_template('ac04data.html', appInfo=appInfo)

@app.route('/ac05data')                               
def ac05data():
        # a = PW_meter.read_3p3w_meter('COM3',1,1)
        appInfo = {  # dict
            'AC05voltage':'{:.2f}'.format(10.00),
            'AC05current':'{:.2f}'.format(11.00),
            'AC05pf':'{:.2f}'.format(12.00),
            'AC05power':'{:.2f}'.format(13.00),
            'AC05consumption':'{:.2f}'.format(14.00),
            'AC05alive':'{:.2f}'.format(15.00),
            'AC05status':'{:.2f}'.format(10.00),
            'AC05mode':'{:.2f}'.format(11.00),
            'AC05settemp':'{:.2f}'.format(12.00),
            'AC05windspeed':'{:.2f}'.format(13.00),
            'AC05roomtemp':'{:.2f}'.format(14.00),
            'AC05alive':'{:.2f}'.format(15.00),        
        }
        return render_template('ac05data.html', appInfo=appInfo)
'''

'''
@app.route('/data/appInfo/<name>', methods=['GET'])
def queryDataMessageByName(name):
    print("type(name) : ", type(name))
    return 'String => {}'.format(name)

@app.route('/data/appInfo/id/<int:id>', methods=['GET'])
def queryDataMessageById(id):
    print("type(id) : ", type(id))
    return 'int => {}'.format(id)

@app.route('/text')
def text():
    return '<html><body><h1>This is Topic</h1></body></html>'
'''


if __name__ == '__main__':

    app.config.from_object(Config())
    
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    first_thread = threading.Thread(target = job2, args=("I am Job2",))
    second_thread = threading.Thread(target = job3, args=("I am Job3",))
    first_thread.start()
    second_thread.start()
    

        
    live_server = Server(app.wsgi_app)
    live_server.watch('**/*.*')
    live_server.serve(open_url_delay=True)

    
