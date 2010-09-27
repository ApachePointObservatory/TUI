#!/usr/bin/env python
"""Supplies test data for the Seeing Monitor

History:
2010-09-24
"""
import math
import random
import RO.PhysConst
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
tuiModel = testDispatcher.tuiModel

Alt = 45.0

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


class GuideOffInfo(object):
    def __init__(self):
        azScale = 1.0 / math.cos(Alt * RO.PhysConst.RadPerDeg)
        lim = 10.0 / RO.PhysConst.ArcSecPerDeg
        mean = 0.0 / RO.PhysConst.ArcSecPerDeg
        sigma = 2.0 / RO.PhysConst.ArcSecPerDeg
        
        self.randomValueDict = dict(
            azOff = RandomValue(-lim * azScale, lim * azScale, mean * azScale, sigma * azScale),
            altOff = RandomValue(-lim, lim, mean, sigma),
            rotOff = RandomValue(-lim, lim, mean, sigma),
        )
    
    def update(self):
        """Randomly change values
        """
        for randomValue in self.randomValueDict.itervalues():
            randomValue.update()
    
    def getValueDict(self):
        """Get a dictionary of value name: value
        """
        return dict((name, randomValue.value) for name, randomValue in self.randomValueDict.iteritems())

    def getKeyVarStr(self):
        """Get the data as a keyword variable
        
        Fields are:
        az off, az vel, az time, alt off, alt vel, alt time, rot off, rot vel, rot time
        where offsets are in degrees
        the offsets are assumed constant so time is not interesting so I don't bother to set it realistically
        """
        return "GuideOff=%(azOff)0.5f, 0.0, 100.0, %(altOff)0.5f, 0.0, 100.0, %(rotOff)0.5f, 0.0, 100.0" % \
            self.getValueDict()

def runTest():
    testDispatcher.dispatch("AxePos=0.0, %0.3f, 0" % (Alt,), actor="tcc")
    _nextGuideOffset(GuideOffInfo(), 2)

def _nextGuideOffset(guideOffInfo, delaySec):
    guideOffInfo.update()
    keyVarStr = guideOffInfo.getKeyVarStr()
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextGuideOffset, guideOffInfo, delaySec)
