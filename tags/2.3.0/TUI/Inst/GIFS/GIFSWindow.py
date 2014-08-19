#!/usr/bin/env python
"""Status/config and exposure windows for GIFS.

History:
2013-09-03 ROwen
"""
import functools

from TUI.Inst.ExposeWdg import ExposeWdg
from TUI.Inst.StatusConfigWdg import StatusConfigWdg
from TUI.Inst.GIFS.StatusConfigInputWdg import StatusConfigInputWdg

InstName = StatusConfigInputWdg.InstName
WindowName = "Inst.%s" % (InstName,)

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "None.%s Expose" % (InstName,),
        defGeom = "+452+280",
        resizable = False,
        wdgFunc = functools.partial(ExposeWdg, instName=InstName),
        visible = False,
    )

    tlSet.createToplevel (
        name = "Inst.%s" % (InstName,),
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = functools.partial(StatusConfigWdg, statusConfigInputClass=StatusConfigInputWdg),
        visible = False,
        doSaveState = True,
    )

if __name__ == "__main__":
    import TestData

    root = TestData.tuiModel.tkRoot
    root.resizable(width=0, height=0)

    tlSet = TestData.tuiModel.tlSet
    addWindow(tlSet)
    tlSet.makeVisible("Inst.%s" % (InstName,))
    
    TestData.start()
    
    root.mainloop()
