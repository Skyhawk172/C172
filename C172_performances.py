import numpy as np
import scipy
from scipy import interpolate
import sys, csv
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
    print "DEPARTURE (%d lbs):" %weight
    print dep_elev,"ft, ",dep_pres,"in. Hg, ",dep_temp,"C" 
    print "Pressure alt.:",dep_pres_alt,"ft"
    print "Density alt. :",dep_dens_alt,"ft\n"

    print "CRUISE (%d lbs):" %weight
    print cruise_alt,"ft, ",cruise_temp,"C, ",RPM,"RPM"
    print "Pressure alt.:",cruise_pres_alt,"ft"
    print "Delta T_std: %+d" %deltaT_std
    print "Density alt. :", cruise_dens_alt,"ft\n"

    print "ARRIVAL (%d lbs):" %weight
    print dest_elev,"ft, ",dest_pres,"in. Hg, ",dest_temp,"C" 
    print "Pressure alt.:",dest_pres_alt,"ft"
    print "Density alt. :",dest_dens_alt,"ft"
    print "---------------------------------"

    roll, clear50ft = takeoff(dep_pres_alt,dep_temp)
    fpm, time, dist, fuel = climb(cruise_alt,cruise_pres_alt,dep_pres_alt,cruise_temp, cruise_std_temp,dep_temp, dep_std_temp)
    mcp, ktas, gph = cruise(RPM,cruise_pres_alt,deltaT_std)
    ldg_roll, ldg_clear50ft = landing(dest_pres,dest_temp)

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



def takeoff(dep_pres_alt,dep_temp):
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

    return f1(dep_pres_alt,dep_temp)[0], f2(dep_pres_alt,dep_temp)[0]


def climb(cruise_alt,cruise_pres_alt,dep_pres_alt,cruise_temp, cruise_std_temp,dep_temp, dep_std_temp):
    table_time= np.array( [ [   0, 730,  0, 0.0,  0],
                            [1000, 695,  1, 0.4,  2],
                            [2000, 655,  3, 0.8,  4],
                            [3000, 620,  4, 1.2,  6],
                            [4000, 600,  6, 1.5,  8],
                            [5000, 550,  8, 1.9, 10],
                            [6000, 505, 10, 2.2, 13],
                            [7000, 455, 12, 2.6, 16],
                            [8000, 410, 14, 3.0, 19] ])

    climb_fpm = np.interp(cruise_pres_alt, table_time[:,0], table_time[:,1])
    climb_time= np.interp(cruise_pres_alt, table_time[:,0], table_time[:,2])
    climb_fuel= np.interp(cruise_pres_alt, table_time[:,0], table_time[:,3])
    climb_dist= np.interp(cruise_pres_alt, table_time[:,0], table_time[:,4])

    start_fpm = np.interp(dep_pres_alt, table_time[:,0], table_time[:,1])
    start_time= np.interp(dep_pres_alt, table_time[:,0], table_time[:,2])
    start_fuel= np.interp(dep_pres_alt, table_time[:,0], table_time[:,3])
    start_dist= np.interp(dep_pres_alt, table_time[:,0], table_time[:,4])

    total_climb_time = climb_time*(1 + (cruise_temp-cruise_std_temp)/100) - start_time* (1 + (dep_temp-dep_std_temp)/100)
    total_climb_dist = climb_dist* (1 + (cruise_temp-cruise_std_temp)/100) - start_dist* (1 + (dep_temp-dep_std_temp)/100)
    total_climb_fuel = climb_fuel* (1 + (cruise_temp-cruise_std_temp)/100) - start_fuel* (1 + (dep_temp-dep_std_temp)/100)

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

    else: print "no data for RPM and altitude"

    return f1(cruise_pres_alt,deltaT_std)[0], f2(cruise_pres_alt,deltaT_std)[0], f3(cruise_pres_alt,deltaT_std)[0]



def landing(dest_pres,dest_temp):
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

    return f1(dest_pres,dest_temp)[0], f2(dest_pres,dest_temp)[0]


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



def auto_weather(tag, id):
    id = id.title()
    if tag==1: print "Connecting to aviationweather.gov/adds"
    url = "http://www.aviationweather.gov/adds/metars?station_ids="\
          +id+"&std_trans=standard&chk_metars=on&hoursStr=most+recent+only&submitmet=Submit"
    page = urllib2.urlopen(url).read()

    metar = page.split(id.upper())[1]
    metar = re.sub('<[^<]+?>', '', metar)
    metar = metar.split()
    try: 
        idx=metar.index("RMK")
        metar = metar[:idx]
    except: pass

    timez=metar[0]
    winds=metar[1]
    viz  =metar[2]
    if "VV" in metar[3] or "FT" in metar[3]: 
        viz   +=" "+metar[3]
        clouds = metar[4:-2]
    else: clouds = metar[3:-2]
    tempdew= metar[-2]
    altset = metar[-1]
    pres = float(altset[-4:])/100.
    temp = int(tempdew[:2])

    return pres, temp, metar


def manual_weather(id):
    print "No connection, please enter values manually \n"

    elev =   int(raw_input("%s elevation [0 ft]: " %id.upper()) or 0)            #ft
    pres = float(raw_input("%s pressure setting [29.92 in Hg]: " %id.upper()) or 29.92) #in. Hg
    temp =   int(raw_input("%s temperature [15 C]: " %id.upper()) or 15)           #Celsius

    return elev, pres, temp


def auto_airport_info(tag, id):
    id = id.title()
    #update at http://ourairports.com/data/
    with open('airports.csv', 'rb') as f:
        reader = csv.reader(f)
        airports = list(reader)
    line = filter(lambda x: id.upper() in x, airports)[0]
    latit, longit, elev = float(line[4]),float(line[5]),int(line[6])
    return elev, latit, longit


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
        try: 
            self.elev, self.lat, self.long = auto_airport_info(self.tag, self.id)
            self.pres, self.temp, self.metar  = auto_weather(self.tag,self.id)
        except: self.elev, self.pres, self.temp = manual_weather(self.id)

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

        self.alt = int(raw_input("Cruise altitude [3000 ft]: ") or 3000)             # ft MSL
        self.temp= int(raw_input("Cruise altitude temperature [9 C]: ") or 9)  # Celsius
        self.RPM        = int(raw_input("Cruise RPM [2300]: ") or 2300)                     #RPM
        self.total_dist=distance(a1,a2)

    def calc(self):
        self.pres_alt = self.alt - (self.av_pres - 29.92)*1000 
        self.std_temp = 15 - (self.alt/1000. * a1.lapse_rate)
        self.deltaT_std      = self.temp - self.std_temp
        self.dens_alt = self.pres_alt + 120*self.deltaT_std

    def climb(self):
        self.fpm, self.time, self.dist, self.fuel = \
            climb(self.alt,self.pres_alt,a1.pres_alt,self.temp, self.std_temp,self.av_temp, self.av_std_temp)

    def cruise(self):
        self.mcp, self.ktas, self.gph = cruise(self.RPM,self.pres_alt,self.deltaT_std)



def display_all(a1,a2,c1):
    print "\033c" #clear screen
    print "---------------------------------"
    print "DEPARTURE %s (%d lbs):" %(a1.id.upper(),a1.weight)
    print a1.elev,"ft, ",a1.pres,"in. Hg, ",a1.temp,"C" 
    print "Pressure alt.:",a1.pres_alt,"ft"
    print "Density alt. :",a1.dens_alt,"ft\n"

    print "CRUISE (%d lbs):" %a1.weight
    print c1.alt,"ft, ",c1.temp,"C, ",c1.RPM,"RPM"
    print "Pressure alt.:",c1.pres_alt,"ft"
    print "Delta T_std: %+d" %c1.deltaT_std
    print "Density alt. :", c1.dens_alt,"ft\n"

    print "ARRIVAL %s (%d lbs):" %(a2.id.upper(),a2.weight)
    print a2.elev,"ft, ",a2.pres,"in. Hg, ",a2.temp,"C" 
    print "Pressure alt.:",a2.pres_alt,"ft"
    print "Density alt. :",a2.dens_alt,"ft\n"

    print "Total distance: %d NM" %c1.total_dist
    print "---------------------------------"


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



if __name__ == '__main__':

    if len(sys.argv)==2 and sys.argv[1]=="-m": 
        manual_inputs()
    else:
        if len(sys.argv)==3:
            depart = sys.argv[1].lower().title()
            destin = sys.argv[2].lower().title()
        else:
            depart = raw_input("Departure airport: ") or "KMTN"
            destin = raw_input("Arrival airport: " ) or "KMTN"


        a1=Airport(1,depart)
        a2=Airport(2,destin)

        a1.calc()
        a1.takeoff()
        a2.calc()
        a2.landing()

        c1=Cruise(a1,a2)
        c1.calc()
        c1.climb()
        c1.cruise()
        
        display_all(a1,a2,c1)
