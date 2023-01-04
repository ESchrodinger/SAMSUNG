import sys
import os
import re
import time,subprocess
from typing import NamedTuple


adb = 'adb -s '
shell = ' shell'

class Info_ps:
    def __init__(self):
        self.USER = ''
        self.PID = 0
        self.PPID = 0
        self.VSZ = 0
        self.RSS = 0
        self.WCHAN = ''
        self.ADDR = 0
        self.S = ''
        self.NAME = ''

class Info_task:
    def __init__(self):
        self.task = ''
        self.activities = []
        
pslist = []        
tasklist = []

appresult = "App,Pid,Task\n"

def getps(device):

    cmd = adb + device + shell + " ps -A"
    allps = subprocess.check_output(cmd)
    
    allps = allps.decode()
    allps = allps.split('\r\n')
    
    
    listsize = len(allps)
    
    #print(allps)
    
    print("allps count " + str(listsize))
    
    for ps in allps:
    
        ps = ps.split()
        
        if len(ps) == 0 or ps[0] == 'USER' :
            continue
        
        psitem = Info_ps()
        
        psitem.USER = ps[0]
        psitem.PID = int(ps[1])
        psitem.PPID = int(ps[2])
        psitem.VSZ = int(ps[3])
        psitem.RSS = int(ps[4])
        psitem.WCHAN = ps[5]
        psitem.ADDR = int(ps[6])
        psitem.S = ps[7]
        psitem.NAME = ps[8]
        
        if (psitem.NAME)[0].isalpha():
            pslist.append(psitem)
            #print(psitem.NAME + ": Pid " + str(psitem.PID))
    


def getactivities(device):

    cmd = adb + device + shell + " dumpsys activity activities"
    alltasks = subprocess.check_output(cmd)
    
    alltasks = alltasks.decode()
    alltasks = alltasks.split('\r\n')
    
    for line in alltasks:
    
        if line.find('* Task{') != -1 :
            task = Info_task()
            task.task = line
            tasklist.append(task)
            #print(line)
        
        if line.find('* Hist') != -1 :
            task.activities.append(line)    
            #print(line)
            
        if line.find('Resumed activities in task display areas') != -1 :
            break

    
if __name__ == '__main__':
    
    print("app " + sys.argv[1])
    
    devices=subprocess.check_output('adb devices')
    devices = devices.decode().split('\r\n')
    
    devicesize = len(devices) - 1
    
    if(devicesize == 0):
        exit(0)
        
    appfile = sys.argv[1] 
    
    applist = open(appfile, 'r', encoding='UTF-8', errors='ignore').read()
    
    applist = applist.split('\n')
    
    #print(applist)
    
    print("applist count " + str(len(applist)))
    
    for i in range(1, devicesize):
        if(len(devices[i]) < 2):
            continue
        end = devices[i].find("\t")
        device = (devices[i])[0:end]
        #print(str(i) + ":" + device)
        
        getps(device)
        
        getactivities(device)
        
        
        for app in applist:
    
            pid = -1
            ptask = None
        
            for ps in pslist :
                if ps.NAME == app :
                    pid = ps.PID
                    break
            
            for task in tasklist :
                if task.task.find(app) != -1 :
                    ptask = task
                    break 
            
                     
            if ptask == None :
                print(app + ' pid: ' + str(pid) + '\n' +  'None' + '\n')
                appresult += (app + ',' + str(pid) + ',' +  'None' + '\n')
            else :
                print(app + ' pid: ' + str(pid) + '\n' +  ptask.task)
                appresult += (app + ',' + str(pid) + ',' +  ptask.task)
                
                for activity in task.activities :
                    print('\n' + activity)
                    appresult += (',' + activity)
                
                print('\n')    
                appresult += '\n'
            
            
            
        timeStr = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        if not os.path.exists(device):
            os.makedirs(device)
        with open(device + os.sep + timeStr + '.csv', 'a') as file:
	        file.write(appresult + '\n')  
    
    
    
    
    
    
    
    