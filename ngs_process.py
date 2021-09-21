import re
import json
import os
import name
import ngs
import numpy as np


def conv_to_rinex(log_name):
    # 21_08_28_06_06_41_SN_TX_txda.rtcm
    #os.system('./convbin  -r rtcm3 -tr 2021/8/22 0:0:0 -n ngs/txda_SmartNet.nav logs/txda_1_nav.rtcm')
    #os.system('./convbin  -r rtcm3 -o ngs/txda_SmartNet.obs logs/txda_1_tx_SmartNet.rtcm')

    if log_name.find('brdc') < 0: 
        log_file = "logs/" + log_name
        obs_file = "ngs/" + log_name.replace(".rtcm", ".obs")
        cmd = './convbin -r rtcm3 -o ' + obs_file + ' ' + log_file
        os.system(cmd)
    else:
        log_file = "logs/" + log_name
        nav_file = "ngs/" + log_name.replace(".rtcm", ".nav")
        date_str = name.datestr_from_file_name(log_name)
        date_str = date_str.split('_')
        date_str = '20' + date_str[0] + '/' + date_str[1] + '/' + date_str[2]
        cmd =  './convbin -r rtcm3 -tr ' + date_str + ' 0:0:0 -n ' + nav_file + ' ' + log_file
        os.system(cmd)


def rnx2rtkp_proc(station_log_rnx, cors_log_rnx, nav_log_rnx):

    try:
        f = open('ngs/' + cors_log_rnx, 'r')
        cors = f.read(10000)    # Don't need to read the whole Rinex file
    except:
        print("No Cors Log for Network")
        return 0

    # Extract the base coordinate, example below
    # -622630.6381 -5330856.2479  3434448.8670                  APPROX POSITION XYZ 
    ref_pos = re.findall(r'(.*)APPROX POSITION', cors)[0]
    
    # Solution file name
    sol_csv = cors_log_rnx.replace('.obs', '.csv')
    
    # ./rnx2rtkp -e -r  -622630.6381 -5330856.2479  3434448.8670 ngs/txda234s.21o ngs/txda_SmartNet.obs  ngs/txda_SmartNet.nav  -o output/txda_TX_SmartNet_Sol.txt
    cmd =   './rnx2rtkp -e -r ' + ref_pos + \
            ' ngs/' + station_log_rnx  + \
            ' ngs/' + cors_log_rnx + \
            ' ngs/' + nav_log_rnx + \
            ' -o ngs/' + sol_csv

    os.system(cmd)
    return 1


def ppk_process(date_code, station_code, network_code):
    cors_file = date_code + '_' + station_code + '_' + network_code + '.obs' 
    station_file = date_code + '_' + station_code + '.obs'
    nav_file = name.datestr_from_file_name(station_file) + '_brdc.nav'  
    success = rnx2rtkp_proc(station_file, cors_file, nav_file)
    print(cors_file, station_file, nav_file)
    return success


def station_process(station_code):
    with open('ngs/' + station_code +'.json') as f:
            station = json.load(f)
    
    logs = station["logs"]

    for log in logs:
        # NAV File

        nav_file = log[0] + '_brdc.rtcm'
        conv_to_rinex(nav_file)

        # OBS File
        cors_file = log[0] + '_' +  station_code + '_' + log[1] + '.rtcm'
        conv_to_rinex(cors_file)

        # Get OBS File From NGS
        # Must be 1 hour later
        ngs.get_ngs_hourly(cors_file)

        success = ppk_process(log[0], station_code, log[1])
        if success:
            station_solution(log[0], station_code, log[1])
   
    f.close()

def station_solution(date_str, station_code, network_code):
        name = date_str + '_' + station_code + '_' + network_code + ".csv"
        data = np.genfromtxt("ngs/" + name,skip_header=20, usecols=(2,3,4,5,6,10), loose=True)
        
        
        clean_data = []
        for row in data:
            if row[0] == 0 or row[1] == 0 or row[2] == 0 and network_code == 'SW':
                continue
            elif row[0] == 0 or row[1] == 0 or row[2] == 0 and row[3] == 1:
                continue
            else:
                clean_data.append(row)
        
        data = np.asarray(clean_data)
 
        if network_code.find('SN') != -1 and network_code != 'SNCA':
            epoch = "2010"
            datum = "NAD83"
        elif network_code == 'SNCA':
            epoch = "2021"
            datum = "NAD83"
        elif network_code == 'VZ':
            epoch = "2010"
            datum = "ITRF"
        else:
            epoch = "2021"
            datum = "ITRF"
        
        with open('ngs/' + station_code +'.json','r') as f:
            station = json.loads(f.read())
            f.close()

        i = 60
        X_avg = np.average(data[i:,0])
        Y_avg = np.average(data[i:,1])
        Z_avg = np.average(data[i:,2])

        X_dev = np.std(data[i:,0])
        Y_dev = np.std(data[i:,1])
        Z_dev = np.std(data[i:,2])

        stats = {   "network" : network_code,
                    "data" : datum,
                    "epoch" : epoch,
                    "convergence_time" : i,
                    "X": X_avg, 
                    "Y": Y_avg,
                    "Z": Z_avg,
                    "X_dev": X_dev,
                    "Y_dev": Y_dev,
                    "Z_dev": Z_dev }
        station["solutions"][date_str] = stats  
        
        json_str = json.dumps(station)
        f = open("ngs/" + station_code + ".json", "w")
        f.write(json_str)
        f.close()



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


for station in stations:
    station_process(station)

