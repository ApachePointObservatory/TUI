#!/usr/bin/env python
"""Supplies test data for the Seeing Monitor

History:
2010-09-24
"""
import random
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
tuiModel = testDispatcher.tuiModel

class RandomValue(object):
    def __init__(self, minValue, maxValue, homeValue, sigma):
        self.minValue = float(minValue)
        self.maxValue = float(maxValue)
        self.homeValue = float(homeValue)
        self.sigma = float(sigma)
        self.value = self.homeValue
        self.update()
    
    def update(self):
        """Randomly change the value
        """
        rawDelta = random.gauss(0, self.sigma)
        proposedValue = self.value + rawDelta

        if proposedValue > self.homeValue:
            probOfFlip = (proposedValue - self.homeValue) / (self.maxValue - self.homeValue)
        else:
            probOfFlip = (self.homeValue - proposedValue) / (self.homeValue - self.minValue)

        if random.random() > probOfFlip:
            self.value -= rawDelta
        else:
            self.value = proposedValue

class StarInfo(object):
    def __init__(self):
        self.randomValueDict = dict(
            fwhm = RandomValue(0.5, 3.0, 1.2, 0.1),
            amplitude = RandomValue(5000, 32000, 10000, 100),
            xCenter = RandomValue(-500, 500, 0, 10),
            yCenter = RandomValue(-500, 500, 0, 10),
        )
    
    def update(self):
        """Randomly change values
        """
        for randomValue in self.randomValueDict.itervalues():
            randomValue.update()
    
    def getValueDict(self):
        """Get a dictionary of value name: value
        """
        valDict = dict((name, randomValue.value) for name, randomValue in self.randomValueDict.iteritems())
        valDict["brightness"] = valDict["fwhm"] * valDict["amplitude"]
        valDict["background"] = 1200.0
        return valDict

    def getKeyVarStr(self):
        """Get the data as a keyword variable

The fields are as follows, where lengths and positions are in binned pixels
and intensities are in ADUs:
0       type characer: c = centroid, f = findstars, g = guide star
1       index: an index identifying the star within the list of stars returned by the command.
2,3     x,yCenter: centroid
4,5     x,yError: estimated standard deviation of x,yCenter
6       radius: radius of centroid region
7       asymmetry: a measure of the asymmetry of the object;
        the value minimized by PyGuide.centroid.
        Warning: not normalized, so probably not much use.
8       FWHM major
9       FWHM minor
10      ellMajAng: angle of ellipse major axis in x,y frame (deg)
11      chiSq: goodness of fit to model star (a double gaussian). From PyGuide.starShape.
12      counts: sum of all unmasked pixels within the centroid radius. From PyGuide.centroid
13      background: background level of fit to model star. From PyGuide.starShape
14      amplitude: amplitude of fit to model star. From PyGuide.starShape
For "g" stars, the two following fields are added:
15,16   predicted x,y position
        """
        return "Star=c, 0, %(xCenter)0.1f, %(yCenter)0.1f, 10.0, -7.0, 5, 100.0, %(fwhm)0.2f, %(fwhm)0.2f, 0, 10, %(brightness)0.1f, %(background)0.1f, %(amplitude)0.1f" % \
            self.getValueDict()


class FocusInfo(object):
    def __init__(self):
        self.randomValueDict = dict(
            fwhm = RandomValue(0.5, 3.0, 1.2, 0.1),
            amplitude = RandomValue(5000, 32000, 10000, 100),
            xCenter = RandomValue(-500, 500, 0, 10),
            yCenter = RandomValue(-500, 500, 0, 10),
        )
    
    def update(self):
        """Randomly change values
        """
        for randomValue in self.randomValueDict.itervalues():
            randomValue.update()
    
    def getValueDict(self):
        """Get a dictionary of value name: value
        """
        valDict = dict((name, randomValue.value) for name, randomValue in self.randomValueDict.iteritems())
        valDict["brightness"] = valDict["fwhm"] * valDict["amplitude"]
        valDict["background"] = 1200.0
        return valDict

    def getKeyVarStr(self):
        """Get the data as a keyword variable

The fields are as follows, where lengths and positions are in binned pixels
and intensities are in ADUs:
0       type characer: c = centroid, f = findstars, g = guide star
1       index: an index identifying the star within the list of stars returned by the command.
2,3     x,yCenter: centroid
4,5     x,yError: estimated standard deviation of x,yCenter
6       radius: radius of centroid region
7       asymmetry: a measure of the asymmetry of the object;
        the value minimized by PyGuide.centroid.
        Warning: not normalized, so probably not much use.
8       FWHM major
9       FWHM minor
10      ellMajAng: angle of ellipse major axis in x,y frame (deg)
11      chiSq: goodness of fit to model star (a double gaussian). From PyGuide.starShape.
12      counts: sum of all unmasked pixels within the centroid radius. From PyGuide.centroid
13      background: background level of fit to model star. From PyGuide.starShape
14      amplitude: amplitude of fit to model star. From PyGuide.starShape
For "g" stars, the two following fields are added:
15,16   predicted x,y position
        """
        return "Star=c, 0, %(xCenter)0.1f, %(yCenter)0.1f, 10.0, -7.0, 5, 100.0, %(fwhm)0.2f, %(fwhm)0.2f, 0, 10, %(brightness)0.1f, %(background)0.1f, %(amplitude)0.1f" % \
            self.getValueDict()

def runTest():
    _nextStar(StarInfo(), 5)
    _nextUserFocus(RandomValue(-500, 500, 0, 10), 6)
    _nextSecPiston(RandomValue(-2000, 2000, 100, 50), 3)

def _nextStar(starInfo, delaySec):
    starInfo.update()
    keyVarStr = starInfo.getKeyVarStr()
    testDispatcher.dispatch(keyVarStr, actor="gcam")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextStar, starInfo, delaySec)
    

def _nextUserFocus(userFocus, delaySec):
    userFocus.update()
    keyVarStr = "SecFocus=%0.1f" % (userFocus.value,)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextUserFocus, userFocus, delaySec)

def _nextSecPiston(secPiston, delaySec):
    secPiston.update()
    keyVarStr = "SecOrient=%0.1f, 0, 0, 0, 0" % (secPiston.value,)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextSecPiston, secPiston, delaySec)
