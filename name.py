
from os import name, stat
import re
import time
import datetime

def name_log(station_name='', network_name='', is_solution=False):
    ts = time.time()
    delta = datetime.timedelta(seconds=18)
    zone = datetime.timezone(offset=delta, name='GPS')
    date_str = datetime.datetime.fromtimestamp(ts, tz=zone).strftime('%y_%m_%d_%H_%M_%S') 

    if is_solution == True:
        log_name = date_str + '_' + station_name + '_' + network_name + '.csv'
    elif station_name != '' and network_name != '':
        log_name = date_str + '_' + station_name + '_' + network_name  + '.rtcm'
    elif station_name != '':
        log_name = date_str + '_' + station_name  + '.rtcm'
    else:
        log_name = date_str + '_brdc.rtcm'
    return log_name


def ngs_rinex_name_daily(station_code):
    ts = time.time()
    ts = ts - 48 * 3600
    file_time = time.gmtime(ts)
    print(file_time.tm_yday)

    # txda2300.21o.gz

    file_name = station_code + \
                str(file_time.tm_yday) + \
                '0.21o.gz'

    # Ref Link for Hourly Observation Data
    # https://noaa-cors-pds.s3.amazonaws.com/rinex/YYYY/DDD/ssss/File-Name

    url = 'https://noaa-cors-pds.s3.amazonaws.com/rinex/2021/' +\
           str(file_time.tm_yday) + '/' + \
           station_code + '/' + \
           file_name    

    return [url, file_name]


# Construction name of NGS Hourly Rinex File
def ngs_rinex_name_hourly(log_name):

    # Example Log Name: 21_08_22_04_14_00_txda_SN.obs

    date_str = datestr_from_file_name(log_name)
    station_name = station_from_file_name(log_name)

    # Example File Name: txda234s.21o
    # Format ssssDDDh.YYo.gz
    # ssss = 4 character station ID
    # DDD = Day of the year 0 - 365
    # h = Hour code  (a=00, b=01, c=02,..,x=23), GPS Time	

    file_time = time.strptime(date_str, '%y_%m_%d_%H_%M_%S')
    file_parts = date_str.split('_')
    print(file_time.tm_yday)
    print(file_time.tm_hour)
    hour_c = chr(file_time.tm_hour + 97)

    file_name = station_name + \
                str(file_time.tm_yday) + \
                chr(file_time.tm_hour + 97) + \
                '.' +  file_parts[0] + "o.gz"

    # Ref Link for Hourly Observation Data
    # https://noaa-cors-pds.s3.amazonaws.com/rinex/YYYY/DDD/ssss/File-Name

    url = 'https://noaa-cors-pds.s3.amazonaws.com/rinex/' +\
           '20' + file_parts[0] + '/' +\
           str(file_time.tm_yday) + '/' + \
           station_name + '/' + \
           file_name    

    return url

def datestr_from_file_name(log_name):
    log_parts = log_name.split('_')
    s = '_'
    date_str = s.join(log_parts[0:6])
    return date_str

def station_from_file_name(log_name):
    log_parts = log_name.split('_')
    station_name = log_parts[6]
    return station_name

#Examples
#print(name_log('txda'))
#print(name_log('txda', 'VZ'))
#print(name_log('txda', 'VZ', True))

