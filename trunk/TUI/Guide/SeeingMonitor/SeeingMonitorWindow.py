#!/usr/bin/env python
"""Seeing monitor

History:
2010-09-27 ROwen    Initial version.
"""
import Tkinter
import RO.Wdg
import RO.Wdg.StripChartWdg
import TUI.Guide.GuideModel
import TUI.TCC.TCCModel

WindowName = "Guide.Seeing Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+22",
        visible = False,
        resizable = True,
        wdgFunc = SeeingMonitorWdg,
    )

class SeeingMonitorWdg(Tkinter.Frame):
    """Monitor guide star information and focus
    """
    FWHMName = "FWHM"
    OneArcsecName = "One Arcsec"
    ZeroName = ""
    BrightnessName = "Brightness"
    SecPistonName = "Sec Piston"
    UserFocusName = "User Focus"
    
    def __init__(self, master, timeRange=7200, width=9, height=4):
        """Create a SeeingMonitorWdg
        
        Inputs:
        - master: parent Tk widget
        - timeRange: range of time displayed (seconds)
        - width: width of plot (inches)
        - hiehgt: height of plot (inches)
        """
        Tkinter.Frame.__init__(self, master)
        
        tccModel = TUI.TCC.TCCModel.getModel()
        
        self.stripChartWdg = RO.Wdg.StripChartWdg.StripChartWdg(
            master = self,
            numSubplots = 3,
            width = width,
            height = height,
            cnvTimeFunc = RO.Wdg.StripChartWdg.TimeConverter(useUTC=True),
        )
        self.stripChartWdg.grid(row=0, column=0, sticky="nwes")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.stripChartWdg.addLine(self.FWHMName, subplotInd=0, color="green")
        self.stripChartWdg.addConstantLine(self.OneArcsecName, 1.0, subplotInd=0, color="purple")
        self.stripChartWdg.addConstantLine(self.ZeroName, 0.0, subplotInd=0, color="black")
        self.stripChartWdg.addLine(self.BrightnessName, subplotInd=1, color="green")
        self.stripChartWdg.addConstantLine(self.ZeroName, 0.0, subplotInd=1, color="black")
        self.stripChartWdg.addLine(self.SecPistonName, subplotInd=2, color="green")
        self.stripChartWdg.addLine(self.UserFocusName, subplotInd=2, color="blue")
        self.stripChartWdg.subplotArr[2].legend(loc=3)
        
        self.stripChartWdg.subplotArr[0].yaxis.set_label_text("FWHM (\")")
        self.stripChartWdg.subplotArr[1].yaxis.set_label_text("Bright (ADU)")
        self.stripChartWdg.subplotArr[2].yaxis.set_label_text("Focus um")

        self.guideModelDict = {} # guide camera name: guide model
        for guideModel in TUI.Guide.GuideModel.modelIter():
            gcamName = guideModel.gcamName
            if gcamName.endswith("focus"):
                continue
            self.guideModelDict[guideModel.gcamName] = guideModel
            guideModel.star.addCallback(self._updStar, callNow=False)

        tccModel.secOrient.addIndexedCallback(self._updSecPiston, 0, callNow=False)
        tccModel.secFocus.addIndexedCallback(self._updUserFocus, 0, callNow=False)
    
    def _addPoint(self, name, value):
        if value == None:
            return
        self.stripChartWdg.addPoint(name, value)
         
    def _updStar(self, valList, isCurrent=True, keyVar=None):
        """Updated star data

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
        if not isCurrent:
            return
        if valList[0] not in ("c", "g"):
            return
        self._addPoint(self.FWHMName, valList[8])
        self._addPoint(self.BrightnessName, valList[12])

    def _updSecPiston(self, val, isCurrent=True, keyVar=None):
        if not isCurrent:
            return
        self._addPoint(self.SecPistonName, val)
    
    def _updUserFocus(self, val, isCurrent=True, keyVar=None):
        if not isCurrent:
            return
        self._addPoint(self.UserFocusName, val)


if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
    TestData.runTest()
    
    TestData.tuiModel.tkRoot.mainloop()
