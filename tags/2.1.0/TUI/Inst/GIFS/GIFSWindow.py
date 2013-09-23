#!/usr/bin/env python
"""Status/config and exposure windows for GIFS.

History:
2013-09-03 ROwen
"""
import TUI.Inst.ExposeWdg

InstName = "GIFS"
WindowName = "Inst.%s" % (InstName,)

def addWindow(tlSet):
    tlSet.createToplevel (
        name = WindowName,
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = GIFSExposeWindow,
        visible = False,
        doSaveState = True,
    )

class GIFSExposeWindow(TUI.Inst.ExposeWdg.ExposeWdg):
    HelpPrefix = 'Instruments/%sWin.html#' % (InstName,)
    def __init__(self, master):
        TUI.Inst.ExposeWdg.ExposeWdg.__init__(self, master, instName=InstName)
        
        self.configWdg.pack_forget()
