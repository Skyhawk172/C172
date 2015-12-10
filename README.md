# C172 Performance Calculator


## Summary 

This Python code calculates various quantities for a Cessna 172M 1976 with a
180-HP engine conversion. The performance quantities are based on the Pilot
Operating Handbook tables, which are interpolated to almost any values based on
user inputs. 

## Disclaimer

The output of this script are intended only as supplementary information and are
not to be used for actual navigation. Any use or misuse of this script and its
consequences are the sole responsibility of the user (i.e. not me, the creator
of the script). Fly safe!


## Input File Description

The performance tables are actually hard-coded in the Python script. The only
external file necessary for running this script is the "airport.csv", which
should be updated or downloaded from http://ourairports.com/data/.



## How to Run

To run the script, simply call: "python C172_performances.py AIRPORT_ID1 AIRPORT_ID2"
For example, one may enter:  "python C172_performances.py KMTN KFKD"

Note that the user can enter more than two airports.

The script will then prompt the user to enter a few values:

* Cruise or leg altitude;
* Cruise RPM (use only a selected number of RPM values)
* Winds aloft station for leg (e.g. EMI)


## Data Processing


## Output

The script outputs a variety of information based on the inputs from the user. 

#### Departure


#### Arrival


#### Climb leg

#### Cruise leg

#### Distance, time, & Wind correction

#### Fuel requirements
