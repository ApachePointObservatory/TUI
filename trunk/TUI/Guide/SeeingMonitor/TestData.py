#!/usr/bin/env python
"""Supplies test data for the Seeing Monitor

History:
2010-09-24
2010-09-29 ROwen    modified to use RO.Alg.RandomWalk
"""
import random
import RO.Alg.RandomWalk
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
tuiModel = testDispatcher.tuiModel

class StarInfo(object):
    def __init__(self):
        self.randomValueDict = dict(
            fwhm = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(1.2, 0.1, 0.5, 3.0),
            amplitude = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(10000, 100, 5000, 32000),
            xCenter = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(0, 10, -500, 500),
            yCenter = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(0, 10, -500, 500),
        )
    
    def update(self):
        """Randomly change values
        """
        for randomValue in self.randomValueDict.itervalues():
            randomValue.next()
    
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
            fwhm = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(0.5, 3.0, 1.2, 0.1),
            amplitude = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(5000, 32000, 10000, 100),
            xCenter = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(-500, 500, 0, 10),
            yCenter = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(-500, 500, 0, 10),
        )
    
    def update(self):
        """Randomly change values
        """
        for randomValue in self.randomValueDict.itervalues():
            randomValue.next()
    
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
    _nextUserFocus(RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(-500, 500, 0, 10), 6)
    _nextSecPiston(RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(-2000, 2000, 100, 50), 3)

def _nextStar(starInfo, delaySec):
    starInfo.update()
    keyVarStr = starInfo.getKeyVarStr()
    testDispatcher.dispatch(keyVarStr, actor="gcam")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextStar, starInfo, delaySec)
    

def _nextUserFocus(userFocus, delaySec):
    keyVarStr = "SecFocus=%0.1f" % (userFocus.next(),)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextUserFocus, userFocus, delaySec)

def _nextSecPiston(secPiston, delaySec):
    keyVarStr = "SecOrient=%0.1f, 0, 0, 0, 0" % (secPiston.next(),)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextSecPiston, secPiston, delaySec)
