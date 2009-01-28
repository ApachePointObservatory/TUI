#!/usr/bin/env python
"""Status/config and exposure windows for Agile.

History:
2008-10-24 ROwen
2009-01-27 ROwen    Added gain, read rate and extSync controls.
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import TUI.Inst.StatusConfigWdg
import StatusConfigInputWdg

InstName = StatusConfigInputWdg.StatusConfigInputWdg.InstName

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "None.%s Expose" % (InstName,),
        defGeom = "+452+280",
        resizable = False,
        wdgFunc = AgileExposeWindow,
        visible = False,
    )
    
    tlSet.createToplevel (
        name = "Inst.%s" % (InstName,),
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = StatusConfigWdg,
        visible = False,
    )

class StatusConfigWdg(TUI.Inst.StatusConfigWdg.StatusConfigWdg):
    def __init__(self, master):
        TUI.Inst.StatusConfigWdg.StatusConfigWdg.__init__(self,
            master = master,
            statusConfigInputClass = StatusConfigInputWdg.StatusConfigInputWdg,
        )

class AgileExposeWindow(TUI.Inst.ExposeWdg.ExposeWdg):
    def __init__(self, master):
        TUI.Inst.ExposeWdg.ExposeWdg.__init__(self, master, instName=InstName)
        gr = self.expInputWdg.gridder
        
        self.gainWdg = RO.Wdg.OptionMenu(
            master = self.expInputWdg,
            items = ("Low", "Medium", "High"),
            defValue = "Medium",
            defMenu = "Default",
            helpText = "CCD amplifier gain",
        )
        gr.gridWdg("Gain", self.gainWdg, colSpan=2)
        
        self.readRateWdg = RO.Wdg.OptionMenu(
            master = self.expInputWdg,
            items = ("Slow", "Fast"),
            defValue = "Fast",
            defMenu = "Default",
            helpText = "CCD readout rate",
        )
        gr.gridWdg("Read Rate", self.readRateWdg, colSpan=2)
        
        self.extSyncWdg = RO.Wdg.Checkbutton(
            master = self.expInputWdg,
            defValue = True,
            helpText = "Use external sync pulse? Yes for best timing.",
        )
        gr.gridWdg("Ext Sync", self.extSyncWdg, colSpan=2)
        
        self.expInputWdg.typeWdgSet.addCallback(self._agileUpdExpType)

    def getExpCmdStr(self):
        """Get exposure command string"""
        cmdStr = self.expInputWdg.getString()
        if cmdStr == None:
            return
        
        cmdStr += " gain=%s readrate=%s" % (self.gainWdg.getString().lower(), self.readRateWdg.getString().lower())
        
        if self.extSyncWdg.getEnable():
            if self.extSyncWdg.getBool():
                extSyncVal = "yes"
            else:
                extSyncVal = "no"
            cmdStr += " extsync=%s" % (extSyncVal,)
        return cmdStr

    def _agileUpdExpType(self, wdg):
        """Exposure type updated; enable or disable external sync control accordingly"""
        expType = self.expInputWdg.getExpType()
        enableExtSync = (expType.lower() != "bias")
        self.extSyncWdg.setEnable(enableExtSync)
        

if __name__ == "__main__":
    import RO.Wdg

    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)
    
    import TestData
    tlSet = TestData.tuiModel.tlSet

    addWindow(tlSet)
    tlSet.makeVisible("Inst.%s" % (InstName,))
    
    TestData.dispatch()
    
    root.mainloop()