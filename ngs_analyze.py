from ngs_collect import collect_for_stations
from operator import ne
from os import stat
import re
import json
import math
import numpy as np
import navpy



def add_opus(station_code):
    f = open("ngs/" + station_code + ".opus", "r")
    opus = f.read()

    X = re.findall("X:(.*)", opus)[0]
    Y = re.findall("Y:(.*)", opus)[0]
    Z = re.findall("Z:(.*)", opus)[0]
    X = X.replace("(m)","")
    Y = Y.replace("(m)","")
    Z = Z.replace("(m)","")

    X = X.split()
    Y = Y.split()
    Z = Z.split()

    Xnad = float(X[0])
    Xnad_dev = float(X[1])
    Xitrf = float(X[2])
    Xitrf_dev = float(X[3])

    Ynad = float(Y[0])
    Ynad_dev = float(Y[1])
    Yitrf = float(Y[2])
    Yitrf_dev = float(Y[3])

    Znad = float(Z[0])
    Znad_dev = float(Z[1])
    Zitrf = float(Z[2])
    Zitrf_dev = float(Z[3])

    deviation = math.sqrt(Xitrf_dev*Xitrf_dev+Yitrf_dev*Yitrf_dev+Zitrf_dev*Zitrf_dev)
    print(deviation)

    datum = {   "X_nad": Xnad, 
                "X_nad_dev": Xnad_dev,
                "X_itrf": Xitrf, 
                "X_itrf_dev": Xitrf_dev,      
                "Y_nad": Ynad, 
                "Y_nad_dev": Ynad_dev, 
                "Y_itrf": Yitrf, 
                "Y_itrf_dev": Yitrf_dev,    
                "Z_nad": Znad, 
                "Z_nad_dev": Znad_dev, 
                "Z_itrf": Zitrf, 
                "Z_itrf_dev": Zitrf_dev     } 
    
    f = open("ngs/" + station_code + ".json", "r")
    station = json.loads(f.read())
    f.close()

    station["opus"] = datum    
    json_str = json.dumps(station)
    
    f = open("ngs/" + station_code + ".json", "w")
    f.write(json_str)
    f.close()

def ecef_dev2ned_dev(rms,lat_ref,lon_ref,alt_ref,latlon_unit='deg',alt_unit='m',model='wgs84'):
    """
    Transform a covariance from ECEF to NED 

    Parameters
    ----------
    ecef_cv : {(N,3)} input array, units of meters*meters
    lat_ref : Reference latitude, unit specified by latlon_unit, default in deg
    lon_ref : Reference longitude, unit specified by latlon_unit, default in deg
    alt_ref : Reference altitude, unit specified by alt_unit, default in m
    
    Returns
    -------
    ned_rms : {(N,3)} array like ned vector, in the ECEF frame, units of meters*meters

    """
    
    C = np.zeros((3,3))
    Cen = np.zeros((3,3))

    if(latlon_unit=='deg'):
        lat_ref = np.deg2rad(lat_ref)
        lon_ref = np.deg2rad(lon_ref)
    elif(latlon_unit=='rad'):
        pass
    else:
        raise ValueError('Input unit unknown')
    
    C[0,0]=-np.sin(lat_ref)*np.cos(lon_ref)
    C[0,1]=-np.sin(lat_ref)*np.sin(lon_ref)
    C[0,2]= np.cos(lat_ref)

    C[1,0]=-np.sin(lon_ref)
    C[1,1]= np.cos(lon_ref)
    C[1,2]= 0

    C[2,0]=-np.cos(lat_ref)*np.cos(lon_ref)
    C[2,1]=-np.cos(lat_ref)*np.sin(lon_ref)
    C[2,2]=-np.sin(lat_ref)

    ecef_cv = np.zeros((3,3))
    ecef_cv[0][0] = rms[0]*rms[0]
    ecef_cv[1][1] = rms[1]*rms[1]
    ecef_cv[2][2] = rms[2]*rms[2]

    ned_cv = np.matmul(C, np.matmul(ecef_cv, C.T))

    ned_rms = np.sqrt([ ned_cv[0][0], ned_cv[1][1], ned_cv[2][2] ])

    return ned_rms

def get_ned_error(sol, station, epoch):
    
    if epoch == 'NAD83,e2010':
        lla_ngs = navpy.ecef2lla([station['X_nad'], station['Y_nad'], station['Z_nad']])
        lla_sol = navpy.ecef2lla([sol['X'], sol['Y'],sol['Z']])
    elif epoch == 'ITRF,e2021':
        lla_ngs = navpy.ecef2lla([station['opus']['X_itrf'], station['opus']['Y_itrf'], station['opus']['Z_itrf']])
        lla_sol = navpy.ecef2lla([sol['X'], sol['Y'],sol['Z']])
    elif epoch == 'ITRF,e2010':
        lla_ngs = navpy.ecef2lla([station['X_itrf'], station['Y_itrf'], station['Z_itrf']])
        lla_sol = navpy.ecef2lla([sol['X'], sol['Y'],sol['Z']])
    elif epoch == 'NAD83,e2021':
        lla_ngs = navpy.ecef2lla([station['opus']['X_nad'], station['opus']['Y_nad'], station['opus']['Z_nad']])
        lla_sol = navpy.ecef2lla([sol['X'], sol['Y'],sol['Z']])

    ned = navpy.lla2ned(lla_ngs[0], lla_ngs[1], lla_ngs[2], lla_sol[0], lla_sol[1], lla_sol[2])
    h_acc = np.sqrt(ned[0]**2 + ned[1]**2)
    ned_dev = ecef_dev2ned_dev([sol["X_dev"], sol["Y_dev"], sol["Z_dev"] ], lla_ngs[0], lla_ngs[1], lla_ngs[2])
    h_dev = np.sqrt(ned_dev[0]**2 + ned_dev[1]**2)
    
    return { "ned" : [ned[0], ned[1], ned[2]],
            "h_acc" : h_acc,
            "h_dev" : h_dev }

def get_ecef_error(sol, station, epoch):

    if epoch == 'NAD83,e2010':
        X_error = sol['X'] - station['X_nad']
        Y_error = sol['Y'] - station['Y_nad']
        Z_error = sol['Z'] - station['Z_nad']
    elif epoch == 'ITRF,e2021':
        X_error = sol['X'] - station['opus']['X_itrf']
        Y_error = sol['Y'] - station['opus']['Y_itrf']
        Z_error = sol['Z'] - station['opus']['Z_itrf']
    elif epoch == 'ITRF,e2010':
        X_error = sol['X'] - station['X_itrf']
        Y_error = sol['Y'] - station['Y_itrf']
        Z_error = sol['Z'] - station['Z_itrf']
    elif epoch == 'NAD83,e2021':
        X_error = sol['X'] - station['opus']['X_nad']
        Y_error = sol['Y'] - station['opus']['Y_nad']
        Z_error = sol['Z'] - station['opus']['Z_nad']
    
    xyz = [X_error, Y_error, Z_error]
    acc = np.linalg.norm(xyz)
    dev = np.linalg.norm([sol['X_dev'],sol['Y_dev'],sol['Z_dev']])

    return { "xyz" : [X_error, Y_error, Z_error],
             "acc" : acc,
             "dev" : dev }


def get_converge_time(station_code, network_code, datestr):
    
    name = datestr + '_' + station_code + '_' + network_code + ".csv"
    try:
        data = np.genfromtxt("ngs/" + name,skip_header=20, usecols=(2,3,4,5,6,10), loose=True)
    except:
        return -1
    
    row_cnt = len(data[:,0])
    if row_cnt < 600:
        return -1
    else:
        x_avg = np.average(data[:,0])
        y_avg = np.average(data[:,1])
        z_avg = np.average(data[:,2])
        r_avg = np.linalg.norm([x_avg,y_avg,z_avg])

    i = 0
    X = 0
    Y = 0
    Z = 0
    for row in data:
        i += 1
        X = np.average(data[:i,0])
        Y = np.average(data[:i,1])
        Z = np.average(data[:i,2])
        R_avg = np.linalg.norm([X,Y,Z])
        if abs(R_avg - r_avg) < 0.3:
            break
    
    return i

def get_fix_rate(station_code, network_code, datestr):

    name = datestr + '_' + station_code + '_' + network_code + ".csv"
    try:
        data = np.genfromtxt("ngs/" + name,skip_header=20, usecols=(2,3,4,5,6,10), loose=True)
    except:
        return 0

    fix_cnt = 0
    total_cnt = 0
    for row in data:
        total_cnt += 1
        if row[3] == 1:
            fix_cnt += 1
        
    return fix_cnt / total_cnt

def analyze_solution(station_code, datestr):
    f = open("ngs/" + station_code + ".json", "r")
    station = json.loads(f.read())
    f.close()

    sol = station["solutions"][datestr]

    fix_rate = get_fix_rate(station_code, sol["network"], datestr)
    converge_time = get_converge_time(station_code, sol["network"], datestr)


    if sol["network"] == 'VZ':
        ecef = get_ecef_error(sol, station, 'ITRF,e2010')
        ned = get_ned_error(sol, station, 'ITRF,e2010')
    elif sol["network"] == 'P1' or sol["network"] == 'SW':
        ecef = get_ecef_error(sol, station, 'ITRF,e2021')
        ned = get_ned_error(sol, station, 'ITRF,e2021')
    elif sol["network"] == 'SNCA':
        ecef = get_ecef_error(sol, station, 'NAD83,e2021')
        ned = get_ned_error(sol, station, 'NAD83,e2021')
    else:    
        ecef = get_ecef_error(sol, station, 'NAD83,e2010')
        ned = get_ned_error(sol, station, 'NAD83,e2010')

    analysis = {    
                    "network" : sol["network"],
                    "error_ecef" : ecef,
                    "error_ned" : ned,
                    "fix_rate" : fix_rate,
                    "convergence_time" : converge_time
                }
    
    station["analysis"][datestr] = analysis

    json_str = json.dumps(station)
    
    f = open("ngs/" + station_code + ".json", "w")
    f.write(json_str)
    f.close()    

def ngs_analyze(station_code):
    f = open("ngs/" + station_code + ".json", "r")
    station = json.loads(f.read())
    f.close()

    solutions = station["solutions"]
    for key in solutions:
        analyze_solution(station_code, key)

def kepler_csv(stations):

    f = open("ngs/kepler.csv", "w")

    header = "latitude,longitude,station_code,SN,VZ,P1,SW\n"
    header = "latitude,longitude,station_code,Accuracy\n"


    f.write(header)

    summary_errors = { 'VZ' : {}, 'SW' : {}, 'SN' : {}, 'P1' :{}}
    for key in summary_errors:
        network_code = key
        summary_errors[network_code] = {"num_points" : 0, 
                                "error_3d" : 0.0, 
                                "error_3d_dev" : 0.0,
                                "error_2d_hor" : 0.0 , 
                                "error_2d_hdev" : 0.0,
                                "error_height" : 0.0,
                                "fix_rate" : 0.0,
                                "convergence_time" : 0.0,
                                "convergence_time_points" : 0.0 } 

    for station_code in stations:
        t = open("ngs/" + station_code + ".json", "r")
        station = json.loads(t.read())
        t.close() 
        lat = station['lat']
        lon = station['lon'] 
        csv_row_errors_3d = { 'SN' : -1, 'VZ' : -1, 'P1' : -1, 'SW' : -1 } 
        analysis = station['analysis']
        for key in analysis:
            result  = analysis[key]
            if result['network'].find('SN') != -1:
                network_code = 'SN'
            else:
                network_code = result['network']
            summary_errors[network_code]['error_3d'] += result['error_ecef']['acc']
            summary_errors[network_code]['error_3d_dev'] += result['error_ecef']['dev']
            summary_errors[network_code]['error_2d_hor'] += result['error_ned']['h_acc']
            summary_errors[network_code]['error_height'] += (result['error_ecef']['acc'] - result['error_ned']['h_acc'])

            summary_errors[network_code]['error_2d_hdev'] += result['error_ned']['h_dev']
            summary_errors[network_code]['fix_rate'] += result['fix_rate']
            summary_errors[network_code]['num_points'] += 1
            if result['convergence_time'] != -1:
                summary_errors[network_code]['convergence_time'] += result['convergence_time']
                summary_errors[network_code]['convergence_time_points'] += 1

            csv_row_errors_3d[network_code] = result['error_ecef']['acc']

        if csv_row_errors_3d['P1'] != -1:
            row = '{0},{1},{2},{3:.2f}\n'.format(lat,lon,station_code, \
                                                csv_row_errors_3d['P1'] )  
            f.write(row)

        '''
        row = '{0},{1},{2},{3},{4},{5},{6}\n'.format(lat,lon,station_code, \
                                               csv_row_errors_3d['SN'], \
                                               csv_row_errors_3d['VZ'], \
                                               csv_row_errors_3d['P1'], \
                                               csv_row_errors_3d['SW'] )  
        '''

        
    
    params = ['error_3d', 'error_3d_dev', 'error_2d_hor', 'error_2d_hdev', 'fix_rate', 'error_height']
    for key in csv_row_errors_3d:
        for param in params:
            summary_errors[key][param] /= summary_errors[key]['num_points'] 
            print("{0},{1},{2:.2f},Num Points: {3}\n".format(key,param,summary_errors[key][param], summary_errors[key]['num_points']))
    
    for key in csv_row_errors_3d:
        summary_errors[key]['convergence_time'] /= summary_errors[key]['convergence_time_points'] 
        print("{0},{1},{2:.2f},Num Points: {3}\n".format(key,'convergence_time',summary_errors[key]['convergence_time'], summary_errors[key]['convergence_time_points']))

    f.close()



#add_opus("txda")
#analyze_solution("txda","21_08_28_19_51_18")
#analyze_solution("txda","21_08_28_19_51_19")
#analyze_solution("txda","21_08_28_19_51_20")
#analyze_solution("txda","21_08_28_19_51_21")

#
#add_opus("wihu")
#ngs_analyze("wihu")
#add_opus("njtw")
#ngs_analyze("njtw")
#add_opus("tn31")
#ngs_analyze("tn31")
#add_opus("ncrd")
#ngs_analyze("ncrd")

stations = ["idpo", "sacr", "wylc", "blom", "ohlc", "pamm","pass","mami","msme","talh", "fmyr","gacc"]

#for station in stations:
#   print(station)
    #add_opus(station)
#    ngs_analyze(station)

#ngs_analyze("momf")
#ngs_analyze("al50")
#ngs_analyze("txlm")
#ngs_analyze("txan")
#ngs_analyze("txlu")
#ngs_analyze("nvbm")
#ngs_analyze("fmyr")


all_stations = [
    "gacc",
    "fmyr",
    "talh",
    "msme",
    "mami",
    "pass",
    "pamm",
    "ohlc",
    "blom",
    "wylc",
    "sacr",
    "idpo",
    "ingy",
    "kybo",
    "garf",
    "mego",
    "mada",
    "gast",
    "scwt",
    "pbch",
    "moip",
    "okdt",
    "mtei",
    "arlr",
    "nvbm",
    "txlu",
    "al50",
    "momf",
    "ncrd",
    "tn31",
    "ict5",
    "mifw",
    "njtw",
    "wihu",
    "sdrc",
    "txda"
]

all_stations = [
    "sacr",
    "okdt",
    "txda",
    "moip",
    "arlr",
    "al50",
    "ingy",
    "tn31",
    "kybo",
    "mifw",
    "ohlc",
    "garf", 
    "njtw",
    "mami",
    "mada",
    "ncrd",
    "gacc",
    "talh",
    "nvbm",
]

all_stations = [
 "idpo",
 "mtei",
 "sdrc",
"txlu",
"wihu",
"ict5",
"momf",
"msme",
"blom",
"pamm",
"pass",
"mego",
"gast",
"scwt", 
"pbch",
"fmyr",
"wylc", 
]

for station in all_stations:
    #print(station)
    #add_opus(station)
   ngs_analyze(station)


kepler_csv(all_stations)
