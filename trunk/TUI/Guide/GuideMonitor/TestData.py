#!/usr/bin/env python
"""Supplies test data for the Seeing Monitor

History:
2010-09-24
2010-09-29 ROwen    modified to use RO.Alg.RandomWalk
"""
import math
import random
import RO.PhysConst
import RO.Alg.RandomWalk
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
tuiModel = testDispatcher.tuiModel

Alt = 45.0

class GuideOffInfo(object):
    def __init__(self):
        azScale = 1.0 / math.cos(Alt * RO.PhysConst.RadPerDeg)
        lim = 10.0 / RO.PhysConst.ArcSecPerDeg
        mean = 0.0 / RO.PhysConst.ArcSecPerDeg
        sigma = 2.0 / RO.PhysConst.ArcSecPerDeg
        
        self.randomValueDict = dict(
            azOff = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(
                mean * azScale, sigma * azScale, -lim * azScale, lim * azScale),
            altOff = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim),
            rotOff = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim),
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
