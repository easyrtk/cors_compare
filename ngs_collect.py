import re
import json
import time
import subprocess
import os
import signal
import name


def  collect_cors_for_ngs_station(cors, station):
      
    f = open("rtkrcv.conf", "r")
    rtkconf = f.read()
    f.close()
    
    input2 = cors["cors_username"] + ':' + cors["cors_password"] + '@' + cors["cors_ip"] + ':' \
         + cors["cors_port"] + '/' + cors["cors_mp"]
    
    rtkconf =(re.sub(r'(inpstr2-path\s+\=)(.*)', r'\g<1>'+input2, rtkconf))

    # Set position to the station of interest
    rtkconf =(re.sub(r'(inpstr2-nmealat\s+\=)(.*)', r'\g<1>'+str(station["lat"]), rtkconf))
    rtkconf =(re.sub(r'(inpstr2-nmealon\s+\=)(.*)', r'\g<1>'+str(station["lon"]), rtkconf))

    log_name = name.name_log(station["name"],cors["cors_name"])
    log2 = 'logs/' + log_name

    log_name = name.name_log()
    log3 = 'logs/' + log_name

    rtkconf =(re.sub(r'(logstr2-path\s+\=)(.*)', r'\g<1>'+log2, rtkconf))
    rtkconf =(re.sub(r'(logstr3-path\s+\=)(.*)', r'\g<1>'+log3, rtkconf))

    f = open("rtkrcv.conf", "w")
    f.write(rtkconf)
    f.close()

    rtklib = subprocess.Popen(['./rtkrcv -s'], shell=True)
    return [log_name, rtklib]

def rtkrcv_proc(station,cors):
    sn_proc = collect_cors_for_ngs_station(cors, station)
    log_name = sn_proc[0]

    station["logs"].append([log_name.replace("_brdc.rtcm", ""), cors["cors_name"]])
    station_name = station["name"]
    json_str = json.dumps(station)
    f = open("ngs/" + station_name + ".json", "w")
    f.write(json_str)
    return sn_proc[1]

def collect_for_stations(stations):
    
    for station in stations:
        networks = ['sn.json', 'vz.json', 'sw.json', 'p1.json']
        #networks = ['sn.json']
        with open('ngs/' + station +'.json') as f:
            station = json.load(f)

        i = 0
        for network in networks:
            i += 1
            with open(network) as f:
                cors = json.load(f)

            if cors["cors_name"] == "SN":
                cors["cors_name"] = "SN" + station["state"]
                cors["cors_ip"] = station["state"].lower() + ".smartnetna.com"
    
            if i == 1:
                process1 = rtkrcv_proc(station,cors)
            elif i == 2:
                process2 = rtkrcv_proc(station,cors)
            elif i == 3:
                process3 = rtkrcv_proc(station,cors)
            else:
                process4 = rtkrcv_proc(station,cors)

            time.sleep(1)

        time.sleep(0.5*3600)
        os.kill(process1.pid,signal.SIGINT)
        time.sleep(1)
        os.kill(process2.pid,signal.SIGINT)

        time.sleep(1)
        os.kill(process3.pid,signal.SIGINT)

        time.sleep(1)
        os.kill(process4.pid,signal.SIGINT)
        time.sleep(1)
    


stations = [
    "fmyr",
    "talh",
    "scwt",
    "gacc",
    "njtw",
    "pass",
    "mami",
    "pamm",
    "ohlc",
    "msme",
    "blom"
]

collect_for_stations(stations)
