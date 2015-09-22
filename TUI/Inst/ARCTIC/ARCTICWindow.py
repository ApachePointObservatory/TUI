#!/usr/bin/env python
"""Status and configuration for ARCTIC.

History:
2015-07-31 CS       Created
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
        wdgFunc = RO.Alg.GenericCallback (
            TUI.Inst.ExposeWdg.ExposeWdg,
            instName = InstName,
        ),
        visible = False,
    )

    tlSet.createToplevel (
        name = "Inst.%s" % (InstName,),
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = StatusConfigWdg,
        visible = False,
        doSaveState = True,
    )

class StatusConfigWdg(TUI.Inst.StatusConfigWdg.StatusConfigWdg):
    def __init__(self, master):
        TUI.Inst.StatusConfigWdg.StatusConfigWdg.__init__(self,
            master = master,
            statusConfigInputClass = StatusConfigInputWdg.StatusConfigInputWdg,
        )

    def _runConfig(self, sr):
        strList = self.inputWdg.getStringList()
        if not strList:
            return
        cmdStr = "set %s" % (" ".join(strList))
        yield sr.waitCmd(
            actor = self.getActorForCommand(cmdStr),
            cmdStr = cmdStr,
        )


if __name__ == "__main__":
    import RO.Wdg
    import RO.Comm.Generic
    RO.Comm.Generic.setFramework("twisted")
    import TestData
    UseTwisted = True

    root = TestData.tuiModel.tkRoot
    root.resizable(width=0, height=0)

    if UseTwisted:
        import twisted.internet.tksupport
        twisted.internet.tksupport.install(root)
        import twisted.internet
        reactor = twisted.internet.reactor

    tlSet = TestData.tuiModel.tlSet
    addWindow(tlSet)
    tlSet.makeVisible("Inst.%s" % (InstName,))

    TestData.start()

    if UseTwisted:
        reactor.run()
    else:
        root.mainloop()
