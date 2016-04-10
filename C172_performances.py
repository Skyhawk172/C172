import numpy as np
import scipy
from scipy import interpolate
import sys, csv, time
import urllib2, re



def calc_quantities(lapse_rate,weight, dep_elev, dep_pres, dep_temp, cruise_alt, cruise_temp, RPM, dest_elev, dest_pres, dest_temp):

    dep_pres_alt    = dep_elev   - (dep_pres - 29.92)*1000 
    cruise_pres_alt = cruise_alt - (np.average([dep_pres,dest_pres]) - 29.92)*1000 
    dest_pres_alt   = dest_elev  - (dest_pres - 29.92)*1000 

    dep_std_temp    = 15 - (dep_elev/1000. * lapse_rate)
    cruise_std_temp = 15 - (cruise_alt/1000. * lapse_rate)
    dest_std_temp   = 15 - (dest_elev/1000. * lapse_rate) 

    dep_dens_alt    = dep_pres_alt  + 120*(dep_temp  - dep_std_temp)
    dest_dens_alt   = dest_pres_alt + 120*(dest_temp - dest_std_temp)
    deltaT_std      = cruise_temp - cruise_std_temp
    cruise_dens_alt = cruise_pres_alt+120*deltaT_std

    print "\033c" #clear screen
    print "---------------------------------"
    print "DEPARTURE (%d ft):" %dep_elev
    print dep_elev,"ft, ",dep_pres,"in. Hg, ",dep_temp,"C" 
    print "Pressure alt.:",dep_pres_alt,"ft"
    print "Density alt. :",dep_dens_alt,"ft\n"

    print "CRUISE (%d lbs):" %weight
    print cruise_alt,"ft, ",cruise_temp,"C, ",RPM,"RPM"
    print "Pressure alt.:",cruise_pres_alt,"ft"
    print "Delta T_std: %+d" %deltaT_std
    print "Density alt. :", cruise_dens_alt,"ft\n"

    print "ARRIVAL (%d ft):" %dest_elev
    print dest_elev,"ft, ",dest_pres,"in. Hg, ",dest_temp,"C" 
    print "Pressure alt.:",dest_pres_alt,"ft"
    print "Density alt. :",dest_dens_alt,"ft"
    print "---------------------------------"

    roll, clear50ft = takeoff(dep_pres_alt,dep_temp)
    fpm, time, dist, fuel = climb(cruise_alt,cruise_pres_alt,dep_pres_alt,cruise_temp, cruise_std_temp,dep_temp, dep_std_temp)
    mcp, ktas, gph = cruise(RPM,cruise_pres_alt,deltaT_std)
    ldg_roll, ldg_clear50ft = landing(dest_pres_alt,dest_temp)

    print 'GRD ROLL    : %d ft'   %roll
    print 'GRD CLR 50FT: %d ft\n' %clear50ft

    print "CLIMB rate: %d fpm" %fpm
    print "CLIMB time: %5.2f min. (to %d ft)" %(time,cruise_alt)
    print "CLIMB dist: %5.2f NM" %dist
    print "CLIMB fuel (incl. taxi):%5.2f gal.\n" %(fuel+1.4)

    print 'CRUISE %%MCP: %d'      %mcp
    print 'CRUISE KTAS: %d'       %ktas
    print 'CRUISE GPH : %5.2f \n' %gph

    print 'LDG GRD ROLL: %d ft'   %ldg_roll
    print 'LDG CLR 50FT: %d ft\n' %ldg_clear50ft


def manual_inputs():

    lapse_rate = 2.   #deg. per 1000 ft
    weight     = 2550 #lbs

    #DEFAULT STARTING VALUES:
    depart    ="KMTN"
    dep_elev  = 22
    dep_pres  = 29.92
    dep_temp  = 15
    
    destin    ="KMTN"
    dest_elev = 22
    dest_pres = 29.92
    dest_temp = 15

    cruise_alt = 3000
    cruise_temp= 9
    RPM        = 2300

    key=''
    while key != 'q':
        #DEPARTURE:
        dep_elev =   int(raw_input("Departure airport elevation [%d ft]: " %dep_elev) or dep_elev)            #ft
        dep_pres = float(raw_input("Departure airport pressure setting [%5.2f in Hg]: " %dep_pres) or dep_pres) #in. Hg
        dep_temp =   int(raw_input("Departure airport temperature [%d C]: " %dep_temp) or dep_temp)           #Celsius

        #ARRIVAL:
        dest_elev = int(raw_input("Arrival airport elevation [%d ft]: " %dest_elev) or dest_elev)           #ft 
        dest_pres = float(raw_input("Arrival airport pressure setting [%5.2f in Hg]: " %dest_pres) or dest_pres) #in. Hg
        dest_temp = int(raw_input("Departure airport temperature [%d C]: " %dest_temp) or dest_temp)         #Celsius

        #CRUISE:
        cruise_alt = int(raw_input("Cruise altitude [%d ft]: " %cruise_alt) or 3000)             # ft MSL
        cruise_temp= int(raw_input("Cruise altitude temperature [%d C]: " %cruise_temp) or 9)  # Celsius
        RPM        = int(raw_input("Cruise RPM [%d]: " %RPM) or 2300)                     #RPM
            
        calc_quantities(lapse_rate,weight, dep_elev, dep_pres, dep_temp, cruise_alt, cruise_temp, RPM, dest_elev, dest_pres, dest_temp)
        key=raw_input("[q] Quit [Enter] Run again: ") or 'r'




def takeoff(pres_alt, temp):
    table_tkoff= np.array([ [ 
                        [   0, 0,  860, 1465],
                        [1000, 0,  940, 1600],
                        [2000, 0, 1025, 1755],
                        [3000, 0, 1125, 1925],
                        [4000, 0, 1235, 2120],
                        [5000, 0, 1355, 2345],
                        [6000, 0, 1495, 2605],
                        [7000, 0, 1645, 2910],
                        [8000, 0, 1820, 3265] ],

                      [ [   0, 10,  925, 1575],
                        [1000, 10, 1010, 1720],
                        [2000, 10, 1110, 1890],
                        [3000, 10, 1215, 2080],
                        [4000, 10, 1335, 2295],
                        [5000, 10, 1465, 2545],
                        [6000, 10, 1615, 2830],
                        [7000, 10, 1785, 3170],
                        [8000, 10, 1970, 3575] ],

                      [ [   0, 20,  995, 1690],
                        [1000, 20, 1090, 1850],
                        [2000, 20, 1195, 2035],
                        [3000, 20, 1310, 2240],
                        [4000, 20, 1440, 2480],
                        [5000, 20, 1585, 2755],
                        [6000, 20, 1745, 3075],
                        [7000, 20, 1920, 3440],
                        [8000, 20, 2120, 3880] ],

                      [ [   0, 30, 1070, 1810],
                        [1000, 30, 1170, 1990],
                        [2000, 30, 1285, 2190],
                        [3000, 30, 1410, 2420],
                        [4000, 30, 1550, 2685],
                        [5000, 30, 1705, 2975],
                        [6000, 30, 1875, 3320],
                        [7000, 30, 2065, 3730],
                        [8000, 30, 2280, 4225] ],  

                      [ [   0, 40, 1150, 1945],
                        [1000, 40, 1260, 2135],
                        [2000, 40, 1380, 2355],
                        [3000, 40, 1515, 2605],
                        [4000, 40, 1660, 2880],
                        [5000, 40, 1825, 3205],
                        [6000, 40, 2010, 3585],
                        [7000, 40, 2215, 4045],
                        [8000, 40, 2450, 4615] ] ])



    x = np.arange(0., 8001, 1000)
    y = np.arange(0.,   41,   10)
    z1 = ( np.asarray([table_tkoff[i,:,2] for i in xrange(5)]) )
    z2 = ( np.asarray([table_tkoff[i,:,3] for i in xrange(5)]) )
    f1 = interpolate.interp2d(x,y,z1, kind='linear')
    f2 = interpolate.interp2d(x,y,z2, kind='linear')

    pres_alt = pres_alt if pres_alt>=0. else 0.
    return f1(pres_alt, temp)[0], f2(pres_alt, temp)[0]


def climb(cruise_alt,cruise_pres_alt,dep_pres_alt,cruise_temp, cruise_std_temp,dep_temp, dep_std_temp):
    table_time= np.array( [ [   0, 730,  0, 0.0,  0],
                            [1000, 695,  1, 0.4,  2],
                            [2000, 655,  3, 0.8,  4],
                            [3000, 620,  4, 1.2,  6],
                            [4000, 600,  6, 1.5,  8],
                            [5000, 550,  8, 1.9, 10],
                            [6000, 505, 10, 2.2, 13],
                            [7000, 455, 12, 2.6, 16],
                            [8000, 410, 14, 3.0, 19],
                            [9000, 360, 17, 3.4, 22],
                            [10000,315, 20, 3.9, 27],
                            [11000,265, 24, 4.4, 32],
                            [12000,220, 28, 5.0, 38] ])

    climb_fpm = np.interp(cruise_pres_alt, table_time[:,0], table_time[:,1])
    climb_time= np.interp(cruise_pres_alt, table_time[:,0], table_time[:,2])
    climb_fuel= np.interp(cruise_pres_alt, table_time[:,0], table_time[:,3])
    climb_dist= np.interp(cruise_pres_alt, table_time[:,0], table_time[:,4])

    dep_pres_alt = dep_pres_alt if dep_pres_alt>=0. else 0.
    start_fpm = np.interp(dep_pres_alt, table_time[:,0], table_time[:,1])
    start_time= np.interp(dep_pres_alt, table_time[:,0], table_time[:,2])
    start_fuel= np.interp(dep_pres_alt, table_time[:,0], table_time[:,3])
    start_dist= np.interp(dep_pres_alt, table_time[:,0], table_time[:,4])

    deltaTc= cruise_temp - cruise_std_temp
    deltaTd= dep_temp    - dep_std_temp
    if deltaTc>0: 
        climb_time *= (1. + (cruise_temp-cruise_std_temp)/100.) 
        climb_dist *= (1. + (cruise_temp-cruise_std_temp)/100.) 
        climb_fuel *= (1. + (cruise_temp-cruise_std_temp)/100.) 
    if deltaTd>0:
        start_time *= (1. + (dep_temp-dep_std_temp)/100.)
        start_dist *= (1. + (dep_temp-dep_std_temp)/100.)
        start_fuel *= (1. + (dep_temp-dep_std_temp)/100.)

    total_climb_time = climb_time - start_time
    total_climb_dist = climb_dist - start_dist
    total_climb_fuel = climb_fuel - start_fuel

    return climb_fpm, total_climb_time, total_climb_dist, total_climb_fuel


def cruise(RPM,cruise_pres_alt,deltaT_std):
    table_2600RPM=np.array([ [ [ 2000,-20, 83, 117, 11.0],
                               [ 4000,-20, 83, 120, 11.1],
                               [ 6000,-20, 78, 120, 10.6],
                               [ 8000,-20, 74, 120, 10.0],
                               [10000,-20, 69, 119,  9.5],
                               [12000,-20, 65, 118,  9.1] ],

                             [ [ 2000,  0, 77, 118, 10.5],
                               [ 4000,  0, 77, 120, 10.4],
                               [ 6000,  0, 73, 119,  9.9],
                               [ 8000,  0, 68, 119,  9.4],
                               [10000,  0, 64, 117,  9.0],
                               [12000,  0, 61, 116,  8.5] ],

                             [ [ 2000, 20, 72, 117,  9.9],
                               [ 4000, 20, 72, 119,  9.8],
                               [ 6000, 20, 68, 118,  9.4],
                               [ 8000, 20, 64, 117,  8.9],
                               [10000, 20, 60, 115,  8.5],
                               [12000, 20, 57, 114,  8.1] ] ])

    table_2500RPM=np.array([ [ [ 2000,-20, 78, 115, 10.6],
                               [ 4000,-20, 74, 115, 10.1],
                               [ 6000,-20, 70, 115,  9.6],
                               [ 8000,-20, 65, 114,  9.1],
                               [10000,-20, 62, 113,  8.7],
                               [12000,-20, 58, 111,  8.3] ],

                             [ [ 2000,  0, 73, 115,  9.9],
                               [ 4000,  0, 69, 115,  9.5],
                               [ 6000,  0, 65, 114,  9.0],
                               [ 8000,  0, 61, 112,  8.6],
                               [10000,  0, 57, 111,  8.2],
                               [12000,  0, 54, 109,  7.8] ],

                             [ [ 2000, 20, 68, 115,  9.4],
                               [ 4000, 20, 64, 114,  8.9],
                               [ 6000, 20, 60, 112,  8.5],
                               [ 8000, 20, 57, 111,  8.1],
                               [10000, 20, 54, 109,  7.8],
                               [12000, 20, 51, 107,  7.4] ] ])



    table_2400RPM=np.array([ [ [ 2000,-20, 69, 111,  9.6],
                               [ 4000,-20, 65, 110,  9.1],
                               [ 6000,-20, 62, 109,  8.6],
                               [ 8000,-20, 58, 108,  8.2],
                               [10000,-20, 55, 106,  7.9],
                               [12000,-20, 52, 105,  7.5] ],

                             [ [ 2000,  0, 64, 110,  9.0],
                               [ 4000,  0, 61, 109,  8.5],
                               [ 6000,  0, 57, 108,  8.2],
                               [ 8000,  0, 54, 106,  7.8],
                               [10000,  0, 51, 104,  7.5],
                               [12000,  0, 49, 102,  7.1] ],

                             [ [ 2000, 20, 60, 109,  8.5],
                               [ 4000, 20, 57, 107,  8.1],
                               [ 6000, 20, 54, 106,  7.7],
                               [ 8000, 20, 51, 104,  7.4],
                               [10000, 20, 49, 102,  7.1],
                               [12000, 20, 46, 100,  6.8] ] ])


    table_2300RPM=np.array([ [ [ 2000,-20, 61, 105,  8.6],
                               [ 4000,-20, 58, 104,  8.2],
                               [ 6000,-20, 54, 103,  7.8],
                               [ 8000,-20, 52, 101,  7.5],
                               [10000,-20, 49, 100,  7.2],
                               [12000,-20, 47,  98,  6.9] ],

                             [ [ 2000,  0, 57, 104,  8.1],
                               [ 4000,  0, 54, 102,  7.7],
                               [ 6000,  0, 51, 101,  7.4],
                               [ 8000,  0, 48,  99,  7.1],
                               [10000,  0, 46,  97,  6.8],
                               [12000,  0, 44,  95,  6.6] ],

                             [ [ 2000, 20, 53, 102,  7.7],
                               [ 4000, 20, 51, 101,  7.3],
                               [ 6000, 20, 48,  99,  7.0],
                               [ 8000, 20, 46,  97,  6.8],
                               [10000, 20, 44,  95,  6.5],
                               [12000, 20, 41,  92,  6.3] ] ])


    table_2200RPM=np.array([ [ [ 2000,-20, 53,  99,  7.7],
                               [ 4000,-20, 51,  98,  7.4],
                               [ 6000,-20, 48,  96,  7.1],
                               [ 8000,-20, 46,  94,  6.8] ],

                             [ [ 2000,  0, 50,  97,  7.3],
                               [ 4000,  0, 48,  96,  7.0],
                               [ 6000,  0, 45,  94,  6.7],
                               [ 8000,  0, 43,  92,  6.5] ],

                             [ [ 2000, 20, 47,  95,  6.9],
                               [ 4000, 20, 45,  94,  6.7],
                               [ 6000, 20, 43,  92,  6.4],
                               [ 8000, 20, 41,  90,  6.2] ] ])


    table_2100RPM=np.array([ [ [ 2000,-20, 47,  92,  6.9],
                               [ 4000,-20, 45,  91,  6.6] ],

                             [ [ 2000,  0, 44,  90,  6.6],
                               [ 4000,  0, 42,  89,  6.4] ],

                             [ [ 2000, 20, 42,  89,  6.3],
                               [ 4000, 20, 40,  87,  6.1] ] ])



    RPM=str(RPM)
    dict_RPM={"2600":table_2600RPM, 
              "2500":table_2500RPM, 
              "2400":table_2400RPM, 
              "2300":table_2300RPM, 
              "2200":table_2200RPM,
              "2100":table_2100RPM}

    while RPM not in dict_RPM: 
        print "RPM not available"
        RPM        =str(raw_input("Cruise RPM [2300]: ") or "2300")      

    xrpm = np.arange(2000., np.max(dict_RPM[RPM][0,:,0])+1, 2000)
    yrpm = np.arange(-20.,   21,   20)

    if cruise_pres_alt <= np.max(xrpm):
        z1 = np.asarray([dict_RPM[RPM][i,:,2] for i in xrange(3)]) 
        z2 = np.asarray([dict_RPM[RPM][i,:,3] for i in xrange(3)]) 
        z3 = np.asarray([dict_RPM[RPM][i,:,4] for i in xrange(3)]) 
        f1 = interpolate.interp2d(xrpm,yrpm,z1, kind='linear')
        f2 = interpolate.interp2d(xrpm,yrpm,z2, kind='linear')
        f3 = interpolate.interp2d(xrpm,yrpm,z3, kind='linear')

    else: 
        print "no data for %s RPM at %d ft" %(RPM, cruise_pres_alt)
        sys.exit()

    return f1(cruise_pres_alt,deltaT_std)[0], f2(cruise_pres_alt,deltaT_std)[0], f3(cruise_pres_alt,deltaT_std)[0]



def landing(pres_alt, temp):
    table_ldg= np.array([ [ [   0, 0,  545, 1290],
                            [1000, 0,  565, 1320],
                            [2000, 0,  585, 1355],
                            [3000, 0,  610, 1385],
                            [4000, 0,  630, 1425],
                            [5000, 0,  655, 1460],
                            [6000, 0,  680, 1500],
                            [7000, 0,  705, 1545],
                            [8000, 0,  735, 1585] ],

                          [ [   0, 10,  565, 1320],
                            [1000, 10,  585, 1350],
                            [2000, 10,  610, 1385],
                            [3000, 10,  630, 1425],
                            [4000, 10,  655, 1460],
                            [5000, 10,  680, 1500],
                            [6000, 10,  705, 1540],
                            [7000, 10,  730, 1585],
                            [8000, 10,  760, 1630] ],

                          [ [   0, 20,  585, 1350],
                            [1000, 20,  605, 1385],
                            [2000, 20,  630, 1420],
                            [3000, 20,  655, 1460],
                            [4000, 20,  675, 1495],
                            [5000, 20,  705, 1535],
                            [6000, 20,  730, 1580],
                            [7000, 20,  760, 1625],
                            [8000, 20,  790, 1670] ],

                          [ [   0, 30,  605, 1380],
                            [1000, 30,  625, 1420],
                            [2000, 30,  650, 1455],
                            [3000, 30,  675, 1495],
                            [4000, 30,  700, 1535],
                            [5000, 30,  725, 1575],
                            [6000, 30,  755, 1620],
                            [7000, 30,  785, 1665],
                            [8000, 30,  815, 1715] ],

                          [ [   0, 40,  625, 1415],
                            [1000, 40,  650, 1450],
                            [2000, 40,  670, 1490],
                            [3000, 40,  695, 1530],
                            [4000, 40,  725, 1570],
                            [5000, 40,  750, 1615],
                            [6000, 40,  780, 1660],
                            [7000, 40,  810, 1705],
                            [8000, 40,  840, 1755] ]  ])

    x = np.arange(0., 8001, 1000)
    y = np.arange(0.,   41,   10)

    z1 = ( np.asarray([table_ldg[i,:,2] for i in xrange(5)]) )
    z2 = ( np.asarray([table_ldg[i,:,3] for i in xrange(5)]) )
    f1 = interpolate.interp2d(x,y,z1, kind='linear')
    f2 = interpolate.interp2d(x,y,z2, kind='linear')

    pres_alt = pres_alt if pres_alt>=0 else 0.
    return f1(pres_alt,temp)[0], f2(pres_alt, temp)[0]


def manual_weather(id):
    print "Error or no connection, please enter values manually \n"

    #elev =   int(raw_input("%s elevation [0 ft]: " %id.upper()) or 0)            #ft
    pres = float(raw_input("%s pressure setting [29.92 in Hg]: " %id.upper()) or 29.92) #in. Hg
    temp =   int(raw_input("%s temperature [15 C]: " %id.upper()) or 15)           #Celsius
    return  pres, temp, [str(pres),"in Hg,  ",str(temp),"C"]


def auto_weather(tag, id, name):
    id = id.title()
    if id[0]!="K" and id[0]!="C": id="K"+id
    if tag==1: print "Connecting to aviationweather.gov/adds \n"
    url = "http://www.aviationweather.gov/adds/metars?station_ids="\
          +id+"&std_trans=standard&chk_metars=on&hoursStr=most+recent+only&submitmet=Submit"
    page = urllib2.urlopen(url).read()
    print name,":"

    metar = page.split(id.upper())[1]
    metar = re.sub('<[^<]+?>', '', metar)
    metar = metar.split()
    print '   ',id.upper(),
    for p in metar: print p,
    print 
    try: 
        idx=metar.index("RMK")
        metar = metar[:idx]
    except: pass
    timez=metar[0]
    if metar[1]=='AUTO': del metar[1]
    winds=metar[1]
    viz  =metar[2]
    if "VV" in metar[3] or "FT" in metar[3]: 
        viz   +=" "+metar[3]
        clouds = metar[4:-2]
    else: clouds = metar[3:-2]
    tempdew= metar[-2]
    altset = metar[-1]
    pres = float(altset[-4:])/100.
    temp = tempdew.split("/")[0]
    if temp[0] == 'M': temp="-"+temp[1:]
    return pres, int(temp), metar


def auto_airport_info(tag, id):
    id = id.title()
    #update at http://ourairports.com/data/
    with open('airports.csv', 'rb') as f:
        reader = csv.reader(f)
        airports = list(reader)
    try: line = filter(lambda x: id.upper() in x, airports)[0]
    except: 
        print 'No airport %s found.' %id.upper()
        sys.exit()
    latit, longit, elev, name = float(line[4]),float(line[5]),int(line[6]), line[3]
    return elev, latit, longit, name


def distance(a1,a2):
    r = 6371/1.86 #Earth's radius in NM
    d_lam = (a1.long - a2.long)*np.pi/180.
    d_phi = (a1.lat - a2.lat)  *np.pi/180.

    d_sig = 2*np.arcsin( np.sqrt( np.sin(d_phi/2)**2 + np.cos(a1.lat*np.pi/180.)*np.cos(a2.lat*np.pi/180.)*np.sin(d_lam/2)**2 ) )
    dist  = r*d_sig #in NM
    
    return np.round(dist)


class Airport():
    def __init__(self,counter,id):
        self.lapse_rate=2
        self.weight    = 2500
        self.tag = counter
        self.id = id

        #url retrieve airport infor & weather
        self.elev, self.lat, self.long, self.name = auto_airport_info(self.tag, self.id)
        try:    self.pres, self.temp, self.metar  = auto_weather(self.tag,self.id, self.name)
        except: self.pres, self.temp, self.metar  = manual_weather(self.id)

    def calc(self):
        self.pres_alt = self.elev   - (self.pres - 29.92)*1000 
        self.std_temp = 15 - (self.elev/1000 * self.lapse_rate)
        self.dens_alt = self.pres_alt + 120*(self.temp - self.std_temp)

    def takeoff(self):
        self.roll, self.clear50ft = takeoff(self.pres_alt, self.temp)

    def landing(self):
        self.ldg_roll, self.ldg_clear50ft = landing(self.pres_alt,self.temp)


class Cruise():
    def __init__(self,a1,a2):
        self.av_pres=np.average([a1.pres,a2.pres])
        self.av_temp=np.average([a1.temp,a2.temp])
        self.av_std_temp=np.average([a1.std_temp,a2.std_temp])

        self.alt=-1
        while self.alt<0 or self.alt>12000:
            self.alt = int(raw_input("\nCruise altitude [3000 ft]: ") or 3000)       # ft MSL
        #self.temp= int(raw_input("Cruise altitude temperature [9 C]: ") or 9)  # Celsius
        self.RPM = int(raw_input("Cruise RPM [2300]: ") or 2300)              #RPM
        self.station=(raw_input("Winds aloft station for leg [EMI]: ") or "EMI").upper()


        self.total_dist=distance(a1,a2)
        self.truecourse=np.round( np.arctan2( (a2.long-a1.long),(a2.lat-a1.lat) )*180/np.pi )
        self.truecourse=self.truecourse if self.truecourse>=0. else self.truecourse+360.
        


    def winds_aloft(self,airport):
        print
        try:
            if self.station[-2:]=="12": 
                url = "http://www.srh.noaa.gov/data/WNO/FD3US3"
                self.station=self.station[:3]
            elif self.station[-2:1]=="24": 
                url = "http://www.srh.noaa.gov/data/WNO/FD5US5"
                self.station=self.station[:3]                
            else: url = "http://www.srh.noaa.gov/data/WNO/FD1US1"
            def_alt=np.array([3000, 6000, 9000, 12000, 18000, 24000, 30000, 34000, 39000])
            winds    =[]
            for line in urllib2.urlopen(url):
                winds.append(line)

            date=filter(lambda x: "DATA" in x, winds)[0].split()
            print ' '.join(date)
            valid=filter(lambda x: "VALID" in x, winds)[0].split()
            print ' '.join(valid)
            data = filter(lambda x: self.station in x, winds)[0].split()
            data.remove(self.station)
            print data

            winds_dir=[None]*len(data)
            winds_vel=[None]*len(data)
            winds_tem=[None]*len(data)
            winds_alt=def_alt[len(def_alt)-len(data):]
            for i in xrange(len(data)-1,-1,-1):
                winds_dir[i]=(float(data[i][:2])*10 if int(data[i][:2])!=99 else 0.)*np.pi/180.
                winds_vel[i]=float(data[i][2:4])
                if winds_alt[i]>24000: 
                    winds_tem[i]=-float(data[i][-2:])
                else: winds_tem[i]=float(data[i][-3:])
                if winds_alt[i]==3000: winds_tem[i]= np.average([airport.temp,winds_tem[i+1]])

            winds_dir = np.unwrap(winds_dir)*180/np.pi
            self.WS   = np.interp(self.alt, winds_alt, winds_vel)
            self.temp = np.interp(self.alt, winds_alt, winds_tem)
            self.WD   = np.round( np.interp(self.alt, winds_alt, winds_dir) )
            if self.WD<0.: self.WD+=360.
        except:
            print "No winds aloft for %s" %self.station
            self.WS = float(raw_input("Wind velocity at %d ft [0 KTS] : " %self.alt) or 0.)
            self.WD = float(raw_input("Wind direction at %d ft [0 deg]: "%self.alt) or 0.)* np.pi/180.
            self.temp= int(raw_input("Cruise temperature [9 C]: ") or 9)  # Celsius

        print "Winds aloft %d ft: %d/%d%+d" %(self.alt,int(self.WD), int(self.WS), int(self.temp))

    def calc_wca(self):
        CRS= self.truecourse *np.pi/180. 
        WD = self.WD *np.pi/180. 
        WS = self.WS

        SWC=(WS/self.ktas)*np.sin(WD-CRS)
        if abs(SWC)>1:
            print "course cannot be flown-- wind too strong"
        else:
            HD=CRS + np.arcsin(SWC)
            if HD<0: HD=HD+2*np.pi
            if (HD>2*np.pi): HD=HD-2*np.pi
            self.GS=self.ktas*np.sqrt(1.-SWC**2) - WS*np.cos(WD-CRS)
            if (self.GS < 0):  "course cannot be flown-- wind too strong"
        self.trueheading = HD*180/np.pi
        angles=np.unwrap([HD,CRS])
        self.wca         =(angles[0]-angles[1])*180/np.pi #(HD-CRS)*180/np.pi
    
    def calc(self, a1):
        self.pres_alt = self.alt - (self.av_pres - 29.92)*1000 
        self.std_temp = 15 - (self.alt/1000. * a1.lapse_rate)
        self.deltaT_std      = self.temp - self.std_temp
        self.dens_alt = self.pres_alt + 120*self.deltaT_std

    def climb(self, a1):
        self.fpm, self.time, self.dist, self.fuel = \
            climb(self.alt,self.pres_alt,a1.pres_alt,self.temp, self.std_temp,self.av_temp, self.av_std_temp)

    def cruise(self):
        self.mcp, self.ktas, self.gph = cruise(self.RPM,self.pres_alt,self.deltaT_std)



def display_all(a1,a2,c1):
    print "---------------------------------------------------"
    print "DEPARTURE %s (%d ft):" %(a1.id.upper(),a1.elev)
    for p in a1.metar: print p,
    print "\nPressure alt.:",a1.pres_alt,"ft"
    print "Density alt. :",a1.dens_alt,"ft\n"

    print "CRUISE (%d lbs):" %a1.weight
    print c1.alt,"ft, ",c1.RPM,"RPM, Winds:","%03d/%d%+d" %(c1.WD, c1.WS, c1.temp)
    print "Pressure alt.:",c1.pres_alt,"ft"
    print "Delta T_std: %+d" %c1.deltaT_std
    print "Density alt. :", c1.dens_alt,"ft\n"

    print "ARRIVAL %s (%d ft):" %(a2.id.upper(),a2.elev)
    for p in a2.metar: print p,
    print "\nPressure alt.:",a2.pres_alt,"ft"
    print "Density alt. :",a2.dens_alt,"ft"
    print "---------------------------------------------------"

    print 'GRD ROLL    : %d ft'   %a1.roll
    print 'GRD CLR 50FT: %d ft\n' %a1.clear50ft

    print "CLIMB rate: %d fpm" %c1.fpm
    print "CLIMB time: %5.2f min. (to %d ft)" %(c1.time,c1.alt)
    print "CLIMB dist: %5.2f NM" %c1.dist
    print "CLIMB fuel (incl. taxi):%5.2f gal.\n" %(c1.fuel+1.4)

    print 'CRUISE %%MCP: %d'      %c1.mcp
    print 'CRUISE KTAS: %d'       %c1.ktas
    print 'CRUISE GPH : %5.2f \n' %c1.gph

    print 'LDG GRD ROLL: %d ft'   %a2.ldg_roll
    print 'LDG CLR 50FT: %d ft\n' %a2.ldg_clear50ft

    print "Total distance: %d NM"    %(c1.total_dist)
    print 'True course   : %d deg'   %np.round(c1.truecourse)
    print 'Wind angle    : %+d deg'  %np.round(c1.wca)
    print 'True heading  : %d deg'   %np.round(c1.trueheading)
    print 'Ground speed  : %d KTS'   %np.round(c1.GS)
    print 'Total time    : %4.2f hrs (%d min.)\n' %(c1.total_dist/c1.GS, c1.total_dist/c1.GS*60)

    print 'FUEL REQUIREMENTS:'
    cruise_time = (c1.total_dist-c1.dist)/c1.GS
    total_fuel  = 1.4 + c1.fuel + cruise_time*c1.gph + 1.4 + c1.gph
    print 'Taxi/Run-up/Takeoff : %5.2f gal.'      %(1.4)
    print 'Climb to %d ft    : %5.2f gal.'        %(c1.alt,c1.fuel)
    print 'Cruise at %d ft   : %5.2f gal.'        %(c1.alt,cruise_time*c1.gph)
    print 'Descent/Pattern/Taxi: %5.2f gal.'      %(1.4)
    print 'VFR reserve         : %5.2f gal.'      %(c1.gph)
    print "--------------------------------"
    print 'TOTAL FUEL          : %5.2f gal.'      %(total_fuel)
    print "--------------------------------"


def display_all2(airports,cruiselegs):
    print "---------------------------------------------------"
    print "DEPARTURE %s (%d ft):" %(airports[0].id.upper(),airports[0].elev)
    for p in airports[0].metar: print p,
    print "\nPressure alt.:",airports[0].pres_alt,"ft"
    print "Density alt. :",airports[0].dens_alt,"ft\n"

    print 'GRD ROLL    : %d ft'   %airports[0].roll
    print 'GRD CLR 50FT: %d ft' %airports[0].clear50ft

    print "---------------------------------------------------"
    print "ARRIVAL %s (%d ft):" %(airports[-1].id.upper(),airports[-1].elev)
    for p in airports[-1].metar: print p,
    print "\nPressure alt.:",airports[-1].pres_alt,"ft"
    print "Density alt. :",airports[-1].dens_alt,"ft\n"

    print 'LDG GRD ROLL: %d ft'   %airports[-1].ldg_roll
    print 'LDG CLR 50FT: %d ft' %airports[-1].ldg_clear50ft
    print "---------------------------------------------------"

    print "CLIMB rate: %d fpm" %cruiselegs[0].fpm
    print "CLIMB time: %5.2f min. (to %d ft)" %(cruiselegs[0].time,cruiselegs[0].alt)
    print "CLIMB dist: %5.2f NM" %cruiselegs[0].dist
    print "CLIMB fuel (incl. taxi):%5.2f gal." %(cruiselegs[0].fuel+1.4)
    print "---------------------------------------------------"

    ic = 1
    for c in cruiselegs:
        print "CRUISE LEG %d: %s --> %s" %(ic, airports[ic-1].id.upper(), airports[ic].id.upper())
        print c.alt,"ft, ",c.RPM,"RPM, Winds:","%03d/%d%+d" %(c.WD, c.WS, c.temp)
        print "Pressure alt.:",c.pres_alt,"ft"
        print "Delta T_std: %+d" %c.deltaT_std
        print "Density alt. :", c.dens_alt,"ft\n"

        print 'CRUISE LEG %d %%MCP: %d'      %(ic, c.mcp)
        print 'CRUISE LEG %d KTAS: %d'       %(ic, c.ktas)
        print 'CRUISE LEG %d GPH : %5.2f \n' %(ic, c.gph)

        print "Total distance: %d NM"    %(c.total_dist)
        print 'True course   : %d deg'   %np.round(c.truecourse)
        print 'Wind angle    : %+d deg'  %np.round(c.wca)
        print 'True heading  : %d deg'   %np.round(c.trueheading)
        print 'Ground speed  : %d KTS'   %np.round(c.GS)
        print 'Total time    : %4.2f hrs (%d min.)' %(c.total_dist/c.GS, c.total_dist/c.GS*60)
        print "---------------------------------------------------"
        ic+=1

    print 'FUEL REQUIREMENTS:'
    print "---------------------------------------------------"
    cruise_fuel = 0
    for c in xrange(len(cruiselegs)):
        if c==0: leg_time = (cruiselegs[c].total_dist-cruiselegs[c].dist)/cruiselegs[c].GS
        else:    leg_time = cruiselegs[c].total_dist/cruiselegs[c].GS

        cruise_fuel += leg_time*cruiselegs[c].gph

    total_fuel = 1.4 + cruiselegs[0].fuel + cruise_fuel + 1.4 + cruiselegs[-1].gph
    print 'Taxi/Run-up/Takeoff : %5.2f gal.'      %(1.4)
    print 'Climb to %d ft    : %5.2f gal.'        %(cruiselegs[0].alt,cruiselegs[0].fuel)
    print 'Total Cruise %d ft: %5.2f gal.'        %(cruiselegs[0].alt,cruise_fuel)
    print 'Descent/Pattern/Taxi: %5.2f gal.'      %(1.4)
    print 'VFR reserve         : %5.2f gal.'      %(cruiselegs[-1].gph)
    print "----------------------------------"
    print 'TOTAL FUEL          : %5.2f gal.'      %(total_fuel)
    print "----------------------------------"
    print "USE CAREFULLY: NOT FOR NAVIGATION"
    print "----------------------------------"



if __name__ == '__main__':


    if len(sys.argv)==2 and sys.argv[1]=="-m": 
        manual_inputs()
    else:
        checkpts=[]
        if len(sys.argv)>=3:
            for i in xrange(1,len(sys.argv)):
                checkpts.append(sys.argv[i].lower().title())
        else:
            checkpts.append(raw_input("Departure airport: ") or "KMTN")
            checkpts.append(raw_input("Arrival airport: ") or "KMTN")

        airports=[]
        for i in xrange(len(checkpts)):
            airports.append(Airport(i+1,checkpts[i]))
            airports[i].calc()

        airports[0].takeoff()
        airports[-1].landing()

        cruiselegs=[]
        for i in xrange(len(airports)-1):
            cruiselegs.append(Cruise(airports[i],airports[i+1]))
            cruiselegs[i].winds_aloft(airports[i])
            cruiselegs[i].calc(airports[i])


        cruiselegs[0].climb(airports[0])
        cruiselegs[0].cruise()
        cruiselegs[0].calc_wca()
        for c in xrange(1,len(cruiselegs)):
            cruiselegs[c].cruise()
            cruiselegs[c].calc_wca()

        display_all2(airports, cruiselegs)

