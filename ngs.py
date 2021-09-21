
import requests
import re
import name
import subprocess
import json
import os

# NGS URL
# https://www.ngs.noaa.gov/cgi-cors/CorsSidebarSelect.prl?site=txda&option=Coordinates14

def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60)
    if direction == 'W' or direction == 'S':
        dd *= -1
    return dd

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

def parse_dms(itrf):    
    itrf = itrf.split() # DD MM SS.SSSS D

    deg = int(itrf[0])
    min = int(itrf[1])
    sec = float(itrf[2])
    dir = str(itrf[3])
    print(deg,min,sec,dir)

    dd = dms2dd(deg,min,sec,dir)
    return dd

def get_ngs_station_coord(station_name):

    # done't remove json that exists
    if os.path.isfile("ngs/" + station_name + ".json"):
        return

    url = 'https://www.ngs.noaa.gov/cgi-cors/CorsSidebarSelect.prl?site=' + station_name + '&option=Coordinates14'
    print(url)
    resp=requests.get(url)

    if resp.status_code==200:

        text = resp.text

        f = open("ngs/" + station_name + ".txt", "w")
        f.write(text)
        f.close()


        itrf_lat = re.search(r'ITRF2014\sPOSITION\s\(EPOCH 2010(.*)?latitude\s+\=\s+([0-9\s\.\sNSWE]+)', text, re.DOTALL)
        itrf_lon = re.search(r'ITRF2014\sPOSITION\s\(EPOCH 2010(.*)?longitude\s+\=\s+([0-9\s\.\sNSWE]+)', text, re.DOTALL)

        X_itrf = re.search(r'ITRF2014\sPOSITION\s\(EPOCH 2010(.*?)X\s\=(.*?)m', text, re.DOTALL)
        X_itrf = float(X_itrf.group(2))
        Y_itrf = re.search(r'ITRF2014\sPOSITION\s\(EPOCH 2010(.*?)Y\s\=(.*?)m', text, re.DOTALL)
        Y_itrf = float(Y_itrf.group(2))
        Z_itrf = re.search(r'ITRF2014\sPOSITION\s\(EPOCH 2010(.*?)Z\s\=(.*?)m', text, re.DOTALL)
        Z_itrf = float(Z_itrf.group(2))

        X_nad = re.search(r'NAD_83\s\(2011\)\sPOSITION\s\(EPOCH 2010(.*?)X\s\=(.*?)m', text, re.DOTALL)
        X_nad = float(X_nad.group(2))
        Y_nad = re.search(r'NAD_83\s\(2011\)\sPOSITION\s\(EPOCH 2010(.*?)Y\s\=(.*?)m', text, re.DOTALL)
        Y_nad = float(Y_nad.group(2))
        Z_nad = re.search(r'NAD_83\s\(2011\)\sPOSITION\s\(EPOCH 2010(.*?)Z\s\=(.*?)m', text, re.DOTALL)
        Z_nad = float(Z_nad.group(2))
      
        pattern = "\(" + station_name.upper() + "\)\,\s\s(.*)"
        state = re.search("%s" % pattern, text)
        state = state.group(1).lower().title()
        state_abbrev = state_lookup(state)

        # ITRF2014\sPOSITION\s\(EPOCH 2010.0\)(.*?)latitude\s+\=\s+([0-9\s\.\NWES]+)
        if itrf_lat:
            lat_dd = parse_dms(itrf_lat.group(2))
            print(lat_dd)
        if itrf_lon:
            lon_dd = parse_dms(itrf_lon.group(2))
            print(lon_dd)

        station_data = {
            "name": station_name,
            "epoch": 2010,
            "state" : state_abbrev,
            "lat":  lat_dd,
            "lon":  lon_dd,
            "X_itrf": X_itrf,
            "Y_itrf": Y_itrf,
            "Z_itrf": Z_itrf,
            "X_nad": X_nad,
            "Y_nad": Y_nad,
            "Z_nad": Z_nad,
            "logs" : [],
            "solutions": {},
            "analysis" : {}
        }

        json_str = json.dumps(station_data)
        f = open("ngs/" + station_name + ".json", "w")
        f.write(json_str)

def get_ngs_daily(station_code):
    info = name.ngs_rinex_name_daily(station_code)
    resp=requests.get(info[0])
    if resp.status_code==200:
        text = resp.content
        f = open("ngs/" + info[1], "wb")
        f.write(text)
        f.close()
        unzip_rinex(info[1])
    print('Downloaded and unzipped ' + info[1])
    info[1] = info[1].replace('.gz', '')
    output = info[1].replace('.21o', '_30s.21o')
    os.system('./convbin  -ti 30 -o ngs/' + output + ' ' + 'ngs/' + info[1])
    print('Converted to 30s ' + output)



def get_ngs_hourly(log_name):
    url = name.ngs_rinex_name_hourly(log_name)
    print(url)
    resp=requests.get(url)
    file_name = re.findall(r'(.*)\_', log_name)[0]
    file_name += '.obs.gz'
    if resp.status_code==200:
        text = resp.content
        f = open("ngs/" + file_name, "wb")
        f.write(text)
        f.close()
        unzip_rinex(file_name)
    else:
       print('no file')

def fetch_ngs_station_from_list(stations):
    for station in stations:
        get_ngs_station_coord(station)

def unzip_rinex(zip_name):
    unzip = subprocess.Popen(["gunzip ngs/" + zip_name], shell=True)
    unzip.wait()

#get_ngs_hourly("21_08_26_04_14_00_txda_SN.obs")
#unzip_rinex("21_08_26_04_14_00_txda.obs.gz")

#get_ngs_station_coord("txda")

def state_lookup(state):

    us_state_abbrev = {
        'Alabama': 'AL',
        'Alaska': 'AK',
        'American Samoa': 'AS',
        'Arizona': 'AZ',
        'Arkansas': 'AR',
        'California': 'CA',
        'Colorado': 'CO',
        'Connecticut': 'CT',
        'Delaware': 'DE',
        'District of Columbia': 'DC',
        'Florida': 'FL',
        'Georgia': 'GA',
        'Guam': 'GU',
        'Hawaii': 'HI',
        'Idaho': 'ID',
        'Illinois': 'IL',
        'Indiana': 'IN',
        'Iowa': 'IA',
        'Kansas': 'KS',
        'Kentucky': 'KY',
        'Louisiana': 'LA',
        'Maine': 'ME',
        'Maryland': 'MD',
        'Massachusetts': 'MA',
        'Michigan': 'MI',
        'Minnesota': 'MN',
        'Mississippi': 'MS',
        'Missouri': 'MO',
        'Montana': 'MT',
        'Nebraska': 'NE',
        'Nevada': 'NV',
        'New Hampshire': 'NH',
        'New Jersey': 'NJ',
        'New Mexico': 'NM',
        'New York': 'NY',
        'North Carolina': 'NC',
        'North Dakota': 'ND',
        'Northern Mariana Islands':'MP',
        'Ohio': 'OH',
        'Oklahoma': 'OK',
        'Oregon': 'OR',
        'Pennsylvania': 'PA',
        'Puerto Rico': 'PR',
        'Rhode Island': 'RI',
        'South Carolina': 'SC',
        'South Dakota': 'SD',
        'Tennessee': 'TN',
        'Texas': 'TX',
        'Utah': 'UT',
        'Vermont': 'VT',
        'Virgin Islands': 'VI',
        'Virginia': 'VA',
        'Washington': 'WA',
        'West Virginia': 'WV',
        'Wisconsin': 'WI',
        'Wyoming': 'WY'
    }

    return us_state_abbrev[state]



#stations = ["idpo", "sacr", "wylc", "blom", "ohlc", "pamm","pass","mami", "pin1","msme","talh", "fmyr","gacc"]

#fetch_ngs_station_from_list(stations)

#get_ngs_daily("ncrd")
