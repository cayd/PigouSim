#Driver

from entity import *
import os
import compileall

compileall.compile_file('C:\\Users\\Cade\\constants.py')

#Initialize Simian
simianEngine = Simian(simName, startTime, endTime, minDelay, useMPI)

simianEngine.addEntity("GridMaster", GridMaster, 0)
pointCount = 1
for city in grid:
    simianEngine.addEntity(getName(city)+"Producer", Producer, pointCount, city)
    simianEngine.addEntity(getName(city)+"City", City, pointCount, city)
    citiesList.append(getName(city))


# this loop should have the cities update the grid every hour of their net power surplus
#looking back, that comment^ is not accurate. it updates as many times as possible in the course of the simulation, not by the hour: CM
#hmmm. actually, it does do what it says it does. not sure why: CM
for i in xrange(int(endTime/minDelay)):
    for j in citiesList:
        simianEngine.schedService(i, "updateDraw", i, j+"City", 1)
        
simianEngine.run()
simianEngine.exit()




#ok. let's work out fi. fi is the population of the city in millions times the avg hourly per capita kW consumption of electricity
#then we add this to a number randomBias * (fi/3 * sin(pi/12 * time)