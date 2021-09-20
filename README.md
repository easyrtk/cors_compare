# Python Framework for Comparing CORS Network Accuracy

This framework uses a set of semi-automated scripts to collect CORS data from multiple CORS networks, and then use RTKLib's post processing tools to compute solutions.  The rovers in the test framework are always NGS Stations with 1-sec GNSS updates - [NGS CORS Map](https://geodesy.noaa.gov/CORS_Map/).  The stations are indentified by a four letter code, e.g., txda.  These are used as rovers because their positions are well establihed and hourly 1-second observation data is freely available.

The processing pipeline consists of three steps:

1. ngs_collect.py - Uses RTKLib CLI *rtkrcv* to collect CORS data from each network relevant for each NGS station in a list.
 
2. ngs_process.py - Uses RTKLib CLD *rnx2rtkp* to process CORS data along with NGS observation data to generate a solution

3. ngs_analyze.py - Compares the Solution to known coordinates, and computes various statistics.  Summarizes results on a Kepler.csv map

The tested networks include SWIFT Skylark, Verizon Hyperprecise, Hexagon SmartNet, and PointOne Polaris.  It is possible to use this code with any NTRIP network.

To use this code, you must have network credentials for the respecitve networks.  The credentials are stored in a simple json file.

`{
    "cors_name": "VZ",
    "cors_ip": "caas.hyperlocation.io", 
    "cors_port": "2100", 
    "cors_mp": "CASTER",
    "cors_username": "<<yourusername>>",
    "cors_password": "<<yourpassword>>"
}`





