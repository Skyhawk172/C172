# C172 Performance Calculator


## Summary 

This Python code calculates various quantities for a Cessna 172M 1976 with a
180-HP engine conversion. The performance quantities are based on the Pilot
Operating Handbook tables, which are interpolated to almost any values based on
user inputs. 

## Disclaimer

The output of this script are intended only as supplementary information and are
not to be used for actual navigation. Always use your Pilot Operating
Handbook. The use or misuse of this script and their consequences are the sole
responsibility of the user (i.e. not me, the creator of the script).  

Fly safe!


## Input File Description

The performance tables from the POH are actually hard-coded in the Python
script. Any modification should therefore be made to the script itself. The
only external file necessary for running this script is the "airport.csv", which
should be updated or downloaded from http://ourairports.com/data/.  The script 
uses the airport identifier to determine the airport elevation and geographic 
location (lat, long) for the waypoint distance calculations.



## How to Use

To run the script, simply call: "python C172_performances.py AIRPORT_ID1 AIRPORT_ID2"
For example, one may enter:  "python C172_performances.py KMTN KFKD"

Note that the user can enter more than two airports.

The script will then prompt the user to enter a few values:

* Cruise or leg altitude [ft];  
* Cruise RPM (use only a selected number of RPM values);  
* Winds aloft station for leg (e.g. EMI; adding the number 3 at the end will use
  the later predicted winds aloft +12/+24 hours).

Additionally, the user can also simply call the script "python
C172_performances.py" and the script will prompt the user to specify the
airports.

Finally, to have full control over the values used in determining the
performance quantities, the user can also use the manual mode with the "-m"
flag: "python C172_performances.py -m". However, this mode does not offer the
Winds Aloft correction or Fuel requirement calculations.


## Data Processing

Based on the user input airport identifiers, the script: 

1. retrieves the METAR weather information for all the airports.  The script
parses temperature and pressure setting from the METAR and determines standard
temperature, pressure altitude, and density altitude;

2. calculates takeoff and landing performance quantities;

3. calculates true course and distance between waypoints;

4. retrieves winds aloft and extrapolates for cruise altitude;

5. calculates cruise performance quantities and wind correction angle;

6. displays all the retrieved and calculation quantities on terminal.



## Output

The script outputs a variety of information based on the inputs from the
user. In particular, the script will the airports' elevation, latest METAR
weather, and derived pressure and density altitudes, along with performance
quantities such as:

* takeoff distances;
* landing distances;
* climb rate, time, distance, and fuel usage;
* cruise %MCP, KTAS, GPH, and wind corrections;
* fuel requirements.

Here is an example of the sections output by the script:

#### Departure

DEPARTURE KMTN (21 ft):  
101345Z 00000KT 1SM BR SKC 06/06 A3003   
Pressure alt.: -89.0 ft  
Density alt. : -1169.0 ft  

GRD ROLL    : 899 ft  
GRD CLR 50FT: 1531 ft  


#### Arrival

ARRIVAL KBWI (146 ft):  
101354Z 00000KT 4SM BR FEW250 07/06 A3001   
Pressure alt.: 56.0 ft  
Density alt. : -904.0 ft  

LDG GRD ROLL: 560 ft  
LDG CLR 50FT: 1312 ft  



#### Climb leg

CLIMB rate: 623 fpm  
CLIMB time:  3.90 min. (to 3000 ft)  
CLIMB dist:  5.80 NM  
CLIMB fuel (incl. taxi): 2.56 gal.  


#### Cruise leg & Wind correction

CRUISE LEG 1: KMTN --> KBWI  
3000 ft,  2300 RPM, Winds: 000/0+5  
Pressure alt.: 2900.0 ft  
Delta T_std: -4  
Density alt. : 2420.0 ft  

CRUISE LEG 1 %MCP: 56  
CRUISE LEG 1 KTAS: 103  
CRUISE LEG 1 GPH :  8.02   

Total distance: 15 NM  
True course   : 239 deg  
Wind angle    : +0 deg  
True heading  : 239 deg  
Ground speed  : 103 KTS  
Total time    : 0.15 hrs (8 min.)  



#### Fuel requirements

Taxi/Run-up/Takeoff :  1.40 gal.  
Climb to 3000 ft    :  1.16 gal.  
Total Cruise 3000 ft:  0.71 gal.  
Descent/Pattern/Taxi:  1.40 gal.  
VFR reserve         :  8.02 gal.  

TOTAL FUEL          : 12.69 gal.  
