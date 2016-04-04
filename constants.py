from SimianPie.simian import Simian, Entity

import matplotlib.pyplot as plt
from matplotlib import collections
from math import *
import random
from scipy.optimize import fsolve
import copy

#minDelay equates to a second
simName, startTime, endTime, minDelay, useMPI = "GRID", 0, 24, 1.0/3600.0, False


#consumption function is in the form of f(Theta)=-Asin(pi/12 Theta)+Fi, with the further simplification that A = Fi/3

#        ID    Location(lat, lon)     String ID(name)    Population in millions   State   priceCurve (explanation in Producer)
grid =  [[1,   [32.7150, 117.1625],   "SanDiego",       1.356,                   "CA",      .5],
         [2,   [34.0500, 118.2500],   "LosAngeles",     18.55,                   "CA",      .5],
         [3,   [38.5556, 121.4689],   "Sacramento",      .48,                     "CA",      .5],
         [4,   [37.7833, 122.4167],   "SanFrancisco",   .837,                    "CA",      .5],
         [5,   [41.8369, 87.6847],    "Chicago",         2.719,                   "IL",      .5],
         [6,   [42.3314, 83.0458],    "Detroit",         .689,                    "MI",      .5],
         [7,   [42.3601, 71.0589],    "Boston",          .646,                    "MA",      .5],
         [8,   [25.7753, 80.2089],    "Miami",           .418,                    "FL",      .5],
         [9,   [40.7127, 74.0059],    "NewYork",        8.406,                   "NY",      .5],
         [10,  [39.8333, 97.4167],    "CENTER",          0,                       "US",      .5]]

#              Voltage    Points connected by lines of such voltage
connectionsWithVoltage = [[750000.0,     (1,2), (1,3), (7,9), (9,5), (9,2)],
                          [500000.0,     (2,3), (5,6), (9,8)],
                          [250000.0,     (1,4)]]              

#the above list ends up pooing all of the voltage values
connections = copy.deepcopy(connectionsWithVoltage)
                 
perCapita = {"US":12146.0,#kWh/capita in 2010 
             "WY":27457.0, 
             "KY":21590.0, 
             "ND":19477.0,
             "LA":18852.0,
             "SC":17903.0,
             "AL":17293.0,
             "WV":17290.0,
             "MS":16793.0,
             "AR":16519.0,
             "IN":16315.0,
             "NE":16293.0,
             "TN":16117.0,
             "OK":15568.0,
             "IA":15048.0,
             "GA":14578.0,
             "VA":14489.0,
             "ID":14475.0,
             "MO":14345.0,
             "NC":14325.0,
             "KS":14263.0,
             "TX":14179.0,
             "MT":13992.0,
             "SD":13916.0,
             "WA":13557.0,
             "OH":13388.0,
             "DE":12904.0,
             "MN":12845.0,
             "NV":12497.0,
             "FL":12379.0,
             "WI":12159.0,
             "OR":12077.0,
             "PA":11759.0,
             "AZ":11395.0,
             "MD":11343.0,
             "IL":11253.0,
             "NM":10739.0,
             "MI":10516.0,
             "CO":10359.0,
             "UT":10106.0,
             "NJ":8985.0,
             "VT":8982.0,
             "ME":8696.0,
             "MA":8591.0,
             "CT":8514.0,
             "NH":8286.0,
             "NY":7467.0,
             "RI":7434.0,
             "CA":6721.0}

rho = 1.7 * 10 **-8 # (copper) ohm m
diameter = .08 # meters (diameter of our wires)
#sets the perCapita dictionary to hourly instead of annual
for key in perCapita:
    perCapita[key] /= (24*365)
    
citiesList = []
# If you use the curve from california you can fit it to be approx. sinusoidal. Then all you need is the average demand around which you oscillate and some idea of amplitude.
# The period and the horizontal shift will remain constant
 
#distance maybe?
def greatCircle(lat1, lon1, lat2, lon2):  
    # convert decimal degrees to radians
    # haversine formula 
    dlat = lat2 - lat1
    dlon = lon2 - lon1  
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r *1000

#straightforward
def getIndex(Id):
    for i in range(len(grid)):
        if grid[i][0] == Id:
            return i
            
#straightforward
def getName(line):
    return line[2]
    
#returns poulation
def getPop(line):
    return line[3]
    
#returns the state of the city 
def getState(line):
    return line[4]
    
#returns priceCurve
def getPriceCurve(line):
    return line[5]
            
#everything will work off the line of the database passed in
def getCoords(line):
    lat1, lon1 = 39.8333, 97.4167 #the approx. center of the continental U.S.
    lat2, lon2 = line[1][0], line[1][1]
    #decimal to radian
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    #calls another function to find distance
    distance = greatCircle(lat1, lon1, lat2, lon2)
    #the math for bearing
    varY = sin(lon2-lon1)*cos(lat2)
    varX = cos(lat1) * sin(lat2) - sin(lat1)*cos(lat2)*cos(lon2-lon1)
    bearing = atan2(varY, varX)
    #converts to measure up from the X-axis instead of down east from true North
    quadrantBearing = ((2*pi)-bearing+(pi/2))%(2*pi)
    #polar to xy 
    xCoord = -1*distance*cos(quadrantBearing)
    yCoord = distance*sin(quadrantBearing)
    return xCoord, yCoord

def findVolts(Id1, Id2):
    for i in connectionsWithVoltage:
        for j in i:
            if j == (Id1, Id2) or j == (Id2, Id1):
                return i[0]

#for use in makeTree. takes a name and finds the accompanying id 
def getId(name):
    for i in range(len(grid)):
        if grid[i][2] == name:
            return grid [i][0]
 
def getNameFromId(Id):
    for i in grid:
        if i[0] == Id:
            return i[2]  
          
#creates and returns a list of ever ycity connected to the one given
def makeTree(name):
    Id = getId(name)
    tree = []
    for i in connections:
        for j in xrange(len(i)): ####
            if i[j][0] == Id:
                tree.append(i[j][1])
            elif i[j][1] == Id:
                tree.append(i[j][0])
    return tree

#passes the coordinates of two given Id's to greatCircle
def getDistance(Id1, Id2):
    index1 = getIndex(Id1)
    index2 = getIndex(Id2)
    lat1 = grid[index1][1][0]
    lon1 = grid[index1][1][1]
    lat2 = grid[index2][1][0]
    lon2 = grid[index2][1][1]
    return greatCircle(lat1, lon1, lat2, lon2)

#the cute little graph
def graph():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    lines = []

    #loops through lines that contain points
    for i in grid: 
        #makes a tuple coorinate pair for the point
        var = getCoords(i)
        #plots the point
        ax.scatter(var[0], var[1])
        #labels the point
        ax.annotate(getName(i), xy=var)

    #creates the list of lines to draw between points
    for i in connections:
        i.pop(0)
        temp = []
        for j in i:
            temp.append([getCoords(grid[getIndex(j[0])]), getCoords(grid[getIndex(j[1])])])
        lines.append(temp)      

    #plots the connecting line segments, for each change in voltage, changes the color. NOTE: does not sort voltages, only goes down the list
    a = 1
    for i in lines:
        lc = collections.LineCollection(i, colors=(0,1/a,0,1), linewidths=2)
        ax.add_collection(lc)
        a += .5

    plt.gca().set_aspect('equal')
    ax.autoscale()
    plt.show()


graph()
