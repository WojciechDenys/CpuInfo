#!/usr/bin/env python3

import os
import time
import subprocess
import ssl
import json
from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

@app.route('/webhook')
def cpuInfo():
    commandCores = subprocess.Popen("cat /proc/cpuinfo | grep processor | wc -l", stdout=subprocess.PIPE, shell=True)
    (coresOut, coresErr) = commandCores.communicate()
    commandModel = subprocess.Popen("cat /proc/cpuinfo | grep 'model name' | head -n1 ", stdout=subprocess.PIPE, shell=True)
    (modelOut, modelErr) = commandModel.communicate()
    modelOut = modelOut[10:].strip()
    
    cpuInfo = {'fulfillmentText': 'Model procesora: ' +  modelOut.decode("utf-8") + ' Liczba rdzeni: ' + coresOut.decode("utf-8") } 
    cpuInfoJSON = json.dumps(cpuInfo)
    #print(cpuInfo)
    return cpuInfoJSON

def cpuStats(counter):
	
    prev_total = 0
    prev_idle = 0
    i = 0
    cpuResults = []
    while i < counter:
		
        command = subprocess.Popen("cat /proc/stat | grep cpu | head -n1 ", stdout=subprocess.PIPE, shell=True, encoding="utf-8")
        (output, err) = command.communicate()
		#print(output)
	
        cpuArr = output
        cpuArr = cpuArr.split(" ")[2:]
		
        total_cpu_since_boot = 0
        total_idle = 0

        for x in range (0, 8):
            total_cpu_since_boot += int(cpuArr[x])
		
        total_idle += int(cpuArr[3])
	
        diff_idle = total_idle - prev_idle
        diff_total = total_cpu_since_boot - prev_total
        diff_usage = (100 *((diff_total-diff_idle)/diff_total))
        if i > 0:	
            cpuResults.append(diff_usage)
        
        prev_total = total_cpu_since_boot
        prev_idle = total_idle
		
        i += 1

        time.sleep(0.1)
	
    result = 0
    for x in range (0, len(cpuResults)):
        result += cpuResults[x]

    result = result/(len(cpuResults))

    result_arr = { 'fulfillmentText': 'Zużycie procesora: ' + str('%.2f' % result) + ' %' }

    resultJSON = json.dumps(result_arr)
    print(result_arr)
    return resultJSON

def ramStats():
    command = subprocess.Popen("free | grep -i 'Mem:'", stdout=subprocess.PIPE, shell=True, encoding="utf-8")
    (out, err) = command.communicate()
    out = out[5:].strip()
    ramArr = out.split(" ")
    ramOut = []
    for x in range(len(ramArr)):
        if ramArr[x] != '':
            if ramArr[x].isdigit() != False:
                ramOut.append(round(float(ramArr[x])/1000))
    totalRam = ramOut[0]
    freeRam = ramOut[2]
    bufforRam = ramOut[4]
    avRam = ramOut[2] + ramOut[4]
    usedRam = totalRam - avRam
    usedRamPer = round((usedRam/totalRam)*100)
    freeRamPer = round((freeRam/totalRam)*100)
    avRamPer = round((avRam/totalRam)*100)
    
    ram_stats = "Całkowita: " + str(totalRam) + ' MB ' + " Wolna: " + str(freeRam) + ' MB ' + " Wolna: " + str(freeRamPer) + ' % ' + " Używana: " + str(usedRam) + ' MB ' +  " Używana: " + str(usedRamPer) + ' % ' +  " Dostępna: " + str(avRam) + ' MB ' + " Dostępna: " +  str(avRamPer) + ' % '
    
    ram_stats = {'fulfillmentText': ram_stats}
    ramJSON = json.dumps(ram_stats)

    return ramJSON

def smbUsers():
    
    smbCommand  = subprocess.Popen("/usr/local/samba/bin/smbstatus | grep 'SMB' | wc -l", stdout=subprocess.PIPE, shell=True)
    (smbOut, smbErr) = smbCommand.communicate()
    smbNo = int(smbOut)
    usrSmbArr = []
    activeSmb = {"activeSmbUsers" : smbNo}
    for x in range(smbNo):
        smbUsrCmd = subprocess.Popen("/usr/local/samba/bin/smbstatus | grep 'SMB' | awk 'NR==%d'" % (x+1), stdout=subprocess.PIPE, shell=True)
        (usrSmbOut, usrSmbErr) = smbUsrCmd.communicate()
        usrSmbArr.append(usrSmbOut)

    for x in range(smbNo):
        usrSmbArr[x] = usrSmbArr[x].decode("utf-8").split(" ")
        
        cleanSmbArr = list(filter(None,usrSmbArr[x]))
        
        activeSmb.update({x : {"user" : cleanSmbArr[1], "ip" : cleanSmbArr[4].strip("()")}})

    activeSmbString = 'Aktywni użytkownicy Samba:  '
    for x in range (smbNo):
        print(activeSmb[0])
        active = activeSmb[0]
        activeSmbString = activeSmbString + ' ' + active['user'] + ' ip: ' + active['ip'] + ' ' 

    activeSmbResponse = {'fulfillmentText': activeSmbString}
    activeSmbJSON = json.dumps(activeSmbResponse)
    
    return activeSmbJSON

def vpnConnections():
    commandCount = subprocess.Popen("/sbin/ifconfig | grep -i 'ppp' | wc -l", stdout=subprocess.PIPE, shell=True)
    (countOut, countErr) = commandCount.communicate()
    
    vpn_conn = str(int(countOut.decode("utf-8")))
    

    vpn_message = {'fulfillmentText': 'Ilość aktywnych użytkowników VPN: ' + vpn_conn}

    vpnJSON = json.dumps(vpn_message)
    
    return vpnJSON

def rebootInfo():

    messege = {'fulfillmentText': 'Uruchamiam ponownie'}

    messegeJSON = json.dumps(messege)

    return messegeJSON

def reboot():

    command = subprocess.Popen(" reboot ", stdout=subprocess.PIPE, shell=True)
    (out, err) = command.communicate()


def results():
    
    req = request.get_json(force=True) 
    action = req.get('queryResult').get('parameters')
    #action = json.load(action[key])
    key = list(action.keys())[0]
    
    if key == 'procesor_info':
        return cpuInfo()
    elif key == 'procesor_zuzycie':
        return cpuStats(2)
    elif key == 'RAM':
        return ramStats()
    elif key == 'VPN_connection':
        return vpnConnections()
    elif key == 'Samba':
        return smbUsers()
    elif key == 'Reboot':
        return rebootInfo()
        #return  reboot()

@app.route('/webhook', methods=['POST'])
def webhook():
    
    return results()

if __name__ == '__main__':
    context = ('domain.crt', 'domain.key')
    app.run(host='192.168.1.101', port=7999, debug=True, ssl_context=context)
