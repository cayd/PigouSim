from constants import *

#The producer Entity
#eventually we'll treat this as an individual, even though it's really all natural gas or whatever firms in the market. so it will need marginal revenue and cost curves: CM
class Producer(Entity):
    def __init__(self, baseInfo, line):
        super(Producer, self).__init__(baseInfo)
        self.line = line
        self.name = getName(line)
        self.pop = getPop(line)
        # the slope of a line that more or less functions as a predictor of output based on price
        # form: kW output = priceCurve * price of power, where priceCurve is currently hardcoded to .5: CM
        self.priceCurve = getPriceCurve(line)
        self.expectedOutput = self.predictOutput()
        self.out.write("Time " + str(self.engine.now) + ": Creating " + self.name + " Producer\n")
    
    #to replace the above function, this should just generate the prediction so it does not have to wait to receive it. it is the same as the city's version
    def predictOutput(self, *args):
        expectedOutput = []
        for time in range(24):
            fi = (getPop(self.line) * 1000000 * float(perCapita[getState(self.line)]))
            expected = (fi/3 * sin(pi/12 * time) + fi) * 1.05 ###new
            expectedOutput.append(expected) 
        self.out.write("Time " + str(self.engine.now) + ": predictOutput occuring at " + self.name + " Producer\n")
        return expectedOutput
            
    #sends to the city, which will form a local net and send to the gridmaster
    def sendProduction(self, *args):
        #print int(self.engine.now), "expectedOutput", self.expectedOutput
        self.reqService(minDelay, "receiveProduction", self.expectedOutput[int(self.engine.now)], self.name+"City", 1)
        self.out.write("Time " + str(self.engine.now) + ": sendProduction occuring at " + self.name + " Producer\n")
        
        
#The city Entity, a combination of city and consumer that serves as the primary reference for all geographically local happenings
class City(Entity):
    def __init__(self, baseInfo, line):
        super(City, self).__init__(baseInfo)
        self.line = line
        self.name = getName(line)
        self.powerDraw = 0
        #this list is the expected draw of the city, with the indexes as the time that draw is expected, e.g. expectedPowerDraw[1] = (expected draw at hour 1)
        self.productionPrediction = []
        self.expectedPowerDraw = self.predictDraw() #### ...what?
        self.powerProduced = 0 # to be updated as nodes send in their power totals: CM
        self.out.write("Time " + str(self.engine.now) + ": Creating " + self.name + " City\n\t" + str(self.expectedPowerDraw) + "\n")
    
    def getDifference(self):
        return self.powerProduced - self.powerDraw
        
    def receiveProduction(self, output, *args):
        self.powerProduced = output
        self.out.write("Time " + str(self.engine.now) + ": receiveProduction occuring at " + self.name + " City\n")
        #once production is received, net is passed on
        self.reqService(minDelay, "sendNet", None, self.name+"City", 1)
        
    #this gives an exact value, not randomized, based on the prediction curve
    def predictDraw(self, *args):
        expectedPowerDraw = []
        for time in range(24):
            fi = (getPop(self.line) * 1000000 * perCapita[getState(self.line)])
            expected = (fi/3 * sin(pi/12 * time) + fi) * 1.05
            expectedPowerDraw.append(expected)
        self.out.write("Time " + str(self.engine.now) + ": predictDraw occuring at " + self.name + " City\n")
        return expectedPowerDraw
        
    #fudges with the expected value to produce what will actually be considered the current consumption in real time
    #this all technically works. you may want to rethink your function though because it is shaped a little oddly
    def updateDraw(self, time, *args):
        fi = (getPop(self.line) * 1000000.0 * perCapita[getState(self.line)])
        randomBias = random.gauss(1,.1) # the fudge: CM
        self.powerDraw = randomBias * (fi/3 * sin(pi/12 * time) + fi)
        self.out.write("Time " + str(self.engine.now) + ": updateDraw occuring at " + self.name + " City\n")
        #every time it updates actual consumption, it should receive production as well and then send the net
        self.reqService(minDelay, "sendProduction", None, self.name+"Producer", 1)
        
    #passes the net consumption of the city to the GridMaster
    def sendNet(self, *args):
        self.reqService(minDelay, "receiveNet", [self.name, self.getDifference()], "GridMaster", 0)
        self.out.write("Time " + str(self.engine.now) + ": sendNet occuring at " + self.name + " City\n")
 


#All part of the findPowerTransferrred function, which implements loss to the highest degree of accuracy
#to be declared as global, since i need to edit them in equations
Vs = 0       
Is = 0
gamma = 0
x = 0  
Zc = 0             

#this puts everything in a format that fsolve() can use. i don't understand it: CM                                                          
def equations(p):
    Vr, Ir = p
    return (cosh(radians(gamma*x))*Vr + Zc*sinh(radians(gamma*x))*Ir - Vs, (1/Zc)*sinh(radians(gamma*x))*Vr + cosh(radians(gamma*x)) * Ir - Is)                    
                                        
                                                
def findPowerTransferred(start, finish, power, num):#waste goes here
    initial = power/num
    global Vs
    Vs = findVolts(start, finish)
    # P = IV
    global Is 
    #now in amps, started in kA #Somewhere in the unit conversion we went from kWh to kW. but i think it's fine because we only have one hour, so the unit should disappear
    Is = 1000 * initial / Vs
    global gamma
    gamma = 1 * 10**-9 #propogation constant. find an exact value 
    global x
    x = getDistance(start, finish)
    global Zc
    Zc = rho * x / ((diameter/2)**2 * pi)
    Vreceived, Ireceived = fsolve(equations, (Vs, Is))
    #outputs watts, kW, whatever it started with
    print "power received", Vreceived* Ireceived / 1000
    print """
    [Vs] = [A  B] [Vr]
    [Is]   [C  D] [Ir]
    """
    print "    [" + str(Vs) + "] = [" + str(cosh(radians(gamma*x))) + "  " + str(Zc*sinh(radians(gamma*x))) + "] [" + str(Vreceived) + "]"
    print "    [" + str(Is) + "]   [" + str((1/Zc)*sinh(radians(gamma*x))) +"  " + str(cosh(radians(gamma*x))) + "] [" + str(Ireceived) + "]\n"
    Ireceived /= 1000 #back to kA
    print "%", (initial- Vreceived*Ireceived)/initial
    return Vreceived* Ireceived 


# keeps track of the grid as a whole, likely the subsidy-adding will be implemented here
class GridMaster(Entity):
    def __init__(self, baseInfo):
        super(GridMaster, self).__init__(baseInfo)
        self.net = 0
        self.netDict = {} #this should just have city names and no producer suffix or whatever
        self.netsReceived = 0
        self.out.write("Time " + str(self.engine.now) + ": Creating Gridmaster\n")# could be an error

        
    #accepts the net draw from the individual cities TODO: record the sender with the net in the netList Dictionary
    def receiveNet(self, net, *args):
        self.net += net[1]
        self.netDict[net[0]] = net[1]
        self.netsReceived += 1
        if self.netsReceived == len(citiesList):
            self.out.write("Time " + str(self.engine.now) + ": GridMaster found net excess to be " + str(self.net) + "\n")
            self.reqService(minDelay, "react", self.net, "GridMaster", 0)
            self.netsReceived = 0
        self.out.write("Time " + str(self.engine.now) + ": receiveNet occuring at GridMaster\n")

            
    #this is called once all of the cities have sent their net consumption
    #it should respond according to this information, redistributing power along the lines necessary, and then reset net
    def react(self, globalNet, *args):
        self.out.write("Time " + str(self.engine.now) + ": react occuring at GridMaster\n")
        print "old", self.netDict
        #WORKAROUNDS!!!!!!: CM
        testing = False
        #if any of the nodes have a shortage, a distribution begins.
        for i in self.netDict:
                if self.netDict[i] < 0:
                    testing = True
        # this part is complicated, but repeats while there is still a shortage somewhere.
        while testing:
            tempDict = {}
            for i in self.netDict:
                tempDict[i] = 0.0 
            for i in self.netDict:
                if self.netDict[i] > 0.0:   
                    destinations = makeTree(i)
                    for j in destinations:
                        print "power sent", self.netDict[i]/float(len(destinations))
                        tempDict[getNameFromId(j)] += findPowerTransferred(getId(i), j, self.netDict[i], float(len(destinations))) # i and j are Id's
            #updates the netDict. if a node was previously negative, the values are added
            #else, we assume that all of the power has been transferred already. so we set to zero, then add the added values
            for i in self.netDict:
                if self.netDict[i] < 0.0:
                    self.netDict[i] += tempDict[i]
                else:
                    self.netDict[i] = tempDict[i] 
            testing = False
            oldNet = self.net
            self.net = 0.00
            for i in self.netDict:
                self.net += self.netDict[i]
                if self.netDict[i] < 0:
                    testing = True
            self.out.write("\tNew net after transfer is " + str(self.net) +"\n\tLosses total " + str(((oldNet-self.net)/oldNet)*100)+ "%\n")
            #this isn't quite what you want. once it realizes we can't settle all counts it decides not to settle any
            if self.net < 0:
                testing = False
                self.out.write("\tGrid is unable to satisfy demands\n")
                
        print "new", self.net, self.netDict
        #reset
        self.net = 0 
        for i in self.netDict:
            self.netDict[i] == 0


#global market curve:
#supply and demand. straightforward
#individual producer: marginal revenue = price, marginal cost swings upward after a certain point.
#^roughly parabolic. let's try making some sort of function for that.
#need to shift it to the right, and we only care about the part that slopes up and where it intersects with the flat line of price
# y = Ax**2 + Bx + C 
# d/dx = 2Ax + B = 0 
#              x = -B/2A
# scrap that. it's hard to shift. for now we'll use a linear model.
# for every $ price increases, quantity increases by .5 kW
#NOTE: these numbers come straight from where the sun don't shine.
#you also have to rearrange how you think about this. You estimate quantity demanded, then select that same quantity to be supplied, then set price accordingly



#extrapolate between the predictions linearly. this is a fair-sized shortcoming, but you haven't even added it yet, so don't worry about that


