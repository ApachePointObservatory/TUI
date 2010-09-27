#!/usr/bin/env python
"""Seeing monitor

History:
2010-09-27 ROwen    Initial version.
"""
import math
import Tkinter
import RO.PhysConst
import RO.Wdg
import RO.Wdg.StripChartWdg
import TUI.Guide.GuideModel
import TUI.TCC.TCCModel

WindowName = "Guide.Guide Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+22",
        visible = False,
        resizable = True,
        wdgFunc = GuideMonitorWdg,
    )

class GuideMonitorWdg(Tkinter.Frame):
    """Monitor guide corrections
    """
    AzOffName = "Az Corr on Sky"
    AltOffName = "Alt Corr"
    ZeroName = ""
    
    def __init__(self, master, timeRange=1800, width=9, height=2.5):
        """Create a GuideMonitorWdg
        
        Inputs:
        - master: parent Tk widget
        - timeRange: range of time displayed (seconds)
        - width: width of plot (inches)
        - hiehgt: height of plot (inches)
        """
        Tkinter.Frame.__init__(self, master)
        
        self.tccModel = TUI.TCC.TCCModel.getModel()
        
        self.stripChartWdg = RO.Wdg.StripChartWdg.StripChartWdg(
            master = self,
            numSubplots = 1,
            width = width,
            height = height,
            cnvTimeFunc = RO.Wdg.StripChartWdg.TimeConverter(useUTC=True),
        )
        self.stripChartWdg.grid(row=0, column=0, sticky="nwes")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.stripChartWdg.addLine(self.AzOffName, subplotInd=0, color="green")
        self.stripChartWdg.addLine(self.AltOffName, subplotInd=0, color="blue")
        self.stripChartWdg.addConstantLine(self.ZeroName, 0.0, subplotInd=0, color="black")
        self.stripChartWdg.subplotArr[0].legend(loc=3, frameon=False)
        
        self.stripChartWdg.subplotArr[0].yaxis.set_label_text("Az/Alt Corr (\")")

        self.guideModelDict = {} # guide camera name: guide model
        for guideModel in TUI.Guide.GuideModel.modelIter():
            gcamName = guideModel.gcamName
            if gcamName.endswith("focus"):
                continue
            self.guideModelDict[guideModel.gcamName] = guideModel
        self.tccModel.guideOff.addCallback(self._updGuideOff, callNow=False)
    
    def _addPoint(self, name, value):
        if value == None:
            return
        self.stripChartWdg.addPoint(name, value)
         
    def _updGuideOff(self, *args, **kargs):
        """Updated actual guide offset in az, alt (")
        """
        if not self.tccModel.guideOff.isCurrent():
            return
        if not self.tccModel.guideOff.isGenuine():
            return

        guideOffPVTList = self.tccModel.guideOff.get()[0]
        guideOffArcSecList = [pvt.getPos() * RO.PhysConst.ArcSecPerDeg for pvt in guideOffPVTList]
        currAlt = self.tccModel.axePos.getInd(1)[0]
        if currAlt == None:
            return
        azOffsetOnSky = guideOffArcSecList[0] * math.cos(currAlt * RO.PhysConst.RadPerDeg)
        
        self._addPoint(self.AzOffName, azOffsetOnSky)
        self._addPoint(self.AltOffName, guideOffArcSecList[1])


if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
    TestData.runTest()
    
    TestData.tuiModel.tkRoot.mainloop()
