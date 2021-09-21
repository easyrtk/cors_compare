# Python Framework for Automated CORS Network Accuracy Comparisons

This framework uses a set of semi-automated scripts to collect CORS data from multiple CORS networks, and then use RTKLib's post processing tools to compute and evaluate PPK solutions using the CORS data.  The rovers in the test framework are always NGS Stations with 1-sec GNSS updates - [NGS CORS Map](https://geodesy.noaa.gov/CORS_Map/).  The stations are indentified by a four letter code, e.g., txda.  Hourly 1-second data files are used as simulated rovers because their data quality and positions are well establihed, the data is freely available, and the procedure is easy to replicate.  The framework was built to support an ION GNSS+ 2021 Paper.  

The utilized RTKLib runtime CLI's (rtkrcv, rnx2rtkp, convbin) are provided in this repo.  They were built for MAC OS.  It is highly likely to use this code these runtimes will need to be recompiled from RTKLib source and replaced. 

The processing pipeline consists of three steps:

1. ngs_collect.py - Uses RTKLib CLI *rtkrcv* to collect CORS data from each network relevant for each NGS station in a list. NTRIP credentials for each network are stored in a JSON file - SN, VZ, SW, and P1 respectively.  You must use your own credentials.  This will store RTCM3 logs in logs directory.  Note, the station must be "added" prior to running, the adding process creates an initialze summary JSON file and gets the station coordinates.  
 
2. ngs_process.py - Uses RTKLib CLI *rnx2rtkp* to do offline RTK with the collected CORS data and NGS observation data (virutal rover) to generate a solution.  All Rinex files as well as the summary JSON file are in the ngs directory. 

3. ngs_analyze.py - Compares the Solution to NGS coordinates (truth), and computes various statistics (ECEF, NED, etc).  Can summarize results for multiple stations in a CSV file that can be furhter visualized with Keper.GL.  

As mentioned above, summaries for each station and network combination are stored in a JSON file.  The JSON file is organized with a set of key:value pairs for the truth data obtained from NGS website and OPUS results.  In addition it has important keys "logs", "solutions", and "analysis".  Each of these keys corresponds to the primary workflow scripts listed above - "logs" for ngs_collect.py, "solutions" for ngs_process.py and "analysis" for ngs_analyze.py.  The JSON file acts as a micro-database of the results collected for each station.    

The ngs.py file provides utilities for grabbing the daily and hourly rover data from NGS archive, as well as automatically reading NGS website for station coordinates, and automatically reading OPUS file results.  OPUS results are used to generate additional data epoch combinations to match up with each network.  name.py establishes some naming conventions so file names can be used as unique keys in the JSON structure.

The tested networks include SWIFT Skylark, Verizon Hyperprecise, Hexagon SmartNet, and PointOne Polaris.  However, it is possible to use this code with any NTRIP network.

To use this code, you must have network credentials for the respecitve networks.  The credentials are stored in a simple json file.  Sample JSON files are provided for each network.  Note Hexagon SmartNet requires a different IP for each state.  This is handled automatically by ngs_collect.py based on the station.  Also note Hexagon SmartNet uses different epochs in high-velocity regions such as CA and WA.  This requires semi-manual adjustment to make accurate comparisons......
 
`{
    "cors_name": "VZ",
    "cors_ip": "caas.hyperlocation.io", 
    "cors_port": "2100", 
    "cors_mp": "CASTER",
    "cors_username": "<<yourusername>>",
    "cors_password": "<<yourpassword>>"
}`

Additional dependencies include numpy and navpy (a nice utility for coordinate conversions)



