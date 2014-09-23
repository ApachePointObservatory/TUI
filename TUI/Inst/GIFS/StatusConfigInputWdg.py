#!/usr/bin/env python
"""Configuration input panel for GIFS.

History:
2014-02-05 ROwen
2014-03-14 ROwen    Added support for help.
"""
import Tkinter
from RO.TkUtil import Timer
import RO.Constants
import RO.MathUtil
import RO.Wdg
import TUI.TUIModel
import GIFSModel

HelpURL = 'Instruments/GIFS/GIFSWin.html'

_DataWidth = 8  # width of data columns
_EnvWidth = 6 # width of environment value columns


class StatusConfigInputWdg (RO.Wdg.InputContFrame):
    InstName = "GIFS"
    HelpPrefix = HelpURL + "#"

    # category names
    ConfigCat = RO.Wdg.StatusConfigGridder.ConfigCat
    EnvironCat = 'environ'

    def __init__(self,
        master,
        stateTracker,
    **kargs):
        """Create a new widget to show status for and configure GIFS

        Inputs:
        - master: parent widget
        - stateTracker: an RO.Wdg.StateTracker
        """
        RO.Wdg.InputContFrame.__init__(self, master=master, stateTracker=stateTracker, **kargs)
        self.model = GIFSModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()
        self.updateStdPresetsTimer = Timer()
        
        self.gridder = RO.Wdg.StatusConfigGridder(
            master = self,
            sticky = "w",
            numStatusCols = 3,
        )

        blankLabel = Tkinter.Label(self, width=_DataWidth)
        blankLabel.grid(row=0, column=1, columnspan=2)

        self.magnifier = StageControls(
            gridder = self.gridder,
            label = "Magnifier",
            configKey = self.model.magnifierConfig,
            statusKey = self.model.magnifierStatus,
        )
    
        self.lenslets = StageControls(
            gridder = self.gridder,
            label = "Lenslets",
            configKey = self.model.lensletsConfig,
            statusKey = self.model.lensletsStatus,
            descr = "lenslet array"
        )

        self.calMirror = CalMirrorControls(
            gridder = self.gridder,
            statusKey = self.model.calMirrorStatus,
        )

        self.filter = FilterControls(
            gridder = self.gridder,
            label = "Filter Wheel",
            configKey = self.model.filterNames,
            statusKey = self.model.filterStatus,
        )

        self.collimator = StageControls(
            gridder = self.gridder,
            label = "Collimator",
            configKey = self.model.collimatorConfig,
            statusKey = self.model.collimatorStatus,
            showOther = True,
        )

        self.disperser = StageControls(
            gridder = self.gridder,
            label = "Disperser",
            configKey = self.model.disperserConfig,
            statusKey = self.model.disperserStatus,
        )

        self.ccdTempWdg = RO.Wdg.FloatLabel(
            master = self,
            formatStr = "%0.1f K",
            helpText = "CCD temperature (K)"
        )
        self.heaterPowerWdg = RO.Wdg.FloatLabel(
            master = self,
            formatStr = "%0.1f %%",
            helpText = "CCD heater power (%)",
        )
        self.gridder.gridWdg(
            label = "CCD Temp",
            dataWdg = (self.ccdTempWdg, self.heaterPowerWdg),
        )

        self.model.ccdTemp.addROWdg(self.ccdTempWdg)
        self.model.heaterPower.addROWdg(self.heaterPowerWdg)

        moveFmtFunc = RO.InputCont.BasicFmt(
            nameSep = " move=",
        )

        # set up the input container set
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = "calmirror",
                    wdgs = self.calMirror.userWdg,
                    formatFunc = RO.InputCont.BasicFmt(nameSep=" "),
                ),
                RO.InputCont.WdgCont (
                    name = "collimator",
                    wdgs = self.collimator.userWdg,
                    formatFunc = moveFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = "disperser",
                    wdgs = self.disperser.userWdg,
                    formatFunc = moveFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = "filter",
                    wdgs = self.filter.userWdg,
                    formatFunc = moveFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = "lenslets",
                    wdgs = self.lenslets.userWdg,
                    formatFunc = moveFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = "magnifier",
                    wdgs = self.magnifier.userWdg,
                    formatFunc = moveFmtFunc,
                ),
            ],
        )

        self._inputContNameKeyVarDict = dict(
            calmirror = self.model.calMirrorPresets,
            collimator = self.model.collimatorPresets,
            disperser = self.model.disperserPresets,
            filter = self.model.filterPresets,
            lenslets = self.model.lensletPresets,
            magnifier = self.model.magnifierPresets,
        )
        
        self.presetsWdg = RO.Wdg.InputContPresetsWdg(
            master = self,
            sysName = "%sConfig" % (self.InstName,),
            userPresetsDict = self.tuiModel.userPresetsDict,
            inputCont = self.inputCont,
            helpText = "use and manage named presets",
            helpURL = self.HelpPrefix + "Presets",
        )
        self.gridder.gridWdg(
            "Presets",
            cfgWdg = self.presetsWdg,
        )

        self.gridder.allGridded()

        # for presets data use a timer to increase the chance that all keywords have been seen
        # before the method is called
        def callUpdPresets(*args, **kwargs):
            self.updateStdPresetsTimer.start(0.1, self.updateStdPresets)
        for keyVar in self._inputContNameKeyVarDict.itervalues():
            keyVar.addCallback(callUpdPresets)
        
        def repaint(evt):
            self.restoreDefault()
        self.bind("<Map>", repaint)

    def updateStdPresets(self):
        """Update standard presets, if the data is available
        """
        self.updateStdPresetsTimer.cancel()
        nameList = self.model.namePresets.get()[0]
        if None in nameList:
            return
        numPresets = len(nameList)
        dataDict = dict()
        for inputContName, keyVar in self._inputContNameKeyVarDict.iteritems():
            valList = keyVar.get()[0]
            if len(valList) != numPresets or None in valList:
                return
            dataDict[inputContName] = valList

        # stdPresets is a dict of name: dict of input container name: value
        stdPresets = dict()
        for i, name in enumerate(nameList):
            contDict = dict()
            for inputContName, valList in dataDict.iteritems():
                if not valList[i]:
                    continue
                contDict[inputContName] = valList[i]
            if contDict:
                stdPresets[name] = contDict
        self.presetsWdg.setStdPresets(stdPresets)


class StageControls(object):
    """A set of widgets that controls one generic GIFS motorized stage
    """
    def __init__(self, gridder, label, configKey, statusKey, descr=None, showOther=False):
        """Construct the widgets, grid them and wire them up

        @param[in] gridder: gridder to use to grid widgets
        @param[in] label: label for this device
        @param[in] configKey: configuration keyword variable; None if none
        @param[in] statusKey: status keyword variable
        @param[in] descr: brief description, for help strings; if None then label.lower()
        @param[in] showOther: show Other... in the menu?
        """
        self.gridder = gridder
        self.label = label
        self.configKey = configKey
        self.statusKey = statusKey
        self.descr = descr if descr is not None else label.lower()
        self._showOther = bool(showOther)
        self.cmdVerb = label.lower().replace(" ", "")
        self._makeWdg()

        if self.configKey:
            self.configKey.addCallback(self.configCallback)
            valueList, isCurrent = configKey.get()
            self.configCallback(valueList, isCurrent)
        self.statusKey.addCallback(self.statusCallback)

    def _makeUserWdg(self):
        """Make the user widget and return it
        """
        return RO.Wdg.OptionMenu(
            master = self.gridder.master,
            items = (),
            autoIsCurrent = True,
            trackDefault = True,
            helpText = "desired position of %s" % (self.descr,),
            helpURL = HelpURL,
        )

    def _makeWdg(self):
        """Make currWdg and userWdg
        """
        if hasattr(self, "currWdg"):
            raise RuntimeError("widgets already exist")

        self.currWdg = RO.Wdg.StrLabel(
            master = self.gridder.master,
            helpText = "current position of %s" % (self.descr,),
            helpURL = HelpURL,
        )

        self.progressBar = RO.Wdg.TimeBar(
            master = self.gridder.master,
        )

        self.userWdg = self._makeUserWdg()

        self.gridder.gridWdg(
            label = self.label,
            dataWdg = (self.currWdg, self.progressBar),
            units = None,
            cfgWdg = self.userWdg,
            colSpan = 1,
        )
        self.progressBar.grid_remove()

    def getCmd(self):
        """Return the command string to command the current user setting, or None if already there
        """
        if self.currWdg.isCurrent():
            return None
        return "%s move=%s" % (self.cmdVerb, self.currWdg.getString())

    def _doOther(self):
        currValue = self.statusKey.getInd(2)[0]
        ob = OtherDialog(
            master = self.gridder.master,
            currValue = currValue,
            descr = self.descr,
        )
        result = ob.result
        if ob.result is None:
            return
        self.userWdg.set(result, forceValid=True)

    def configCallback(self, valueList, isCurrent, keyVar=None):
        """Config updated
        """
        self.userWdg.setItems(
            items = sorted(valueList),
            isCurrent = isCurrent,
            checkCurrent = True,
            checkDef = False,
        )
        if self._showOther:
            menu = self.userWdg.getMenu()
            menu.add_command(
                label = "Other...",
                command = self._doOther,
            )

    def statusCallback(self, valueList, isCurrent, keyVar=None):
        """Status updated
        """
        isMoving = valueList[0]
        currPos = valueList[1]
        moveDuration = valueList[6]
        self.currWdg.set(currPos, isCurrent=isCurrent)
        if isMoving and moveDuration > 0:
            self.progressBar.start(value=moveDuration, newMax=moveDuration)
            self.progressBar.grid()
        else:
            self.progressBar.grid_remove()
            self.userWdg.setDefault(currPos, isCurrent=isCurrent, doCheck=False)

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.label)


class CalMirrorControls(StageControls):
    def __init__(self, gridder, statusKey):
        StageControls.__init__(self,
            gridder = gridder,
            label = "Cal Mirror",
            configKey = None,
            statusKey = statusKey,
            descr = "calibration mirror",
        )

    def _makeUserWdg(self):
        """Make the user widget and return it
        """
        return RO.Wdg.Checkbutton(
            master = self.gridder.master,
            offvalue = "out",
            onvalue = "in",
            showValue = True,
            trackDefault = True,
            helpText = "desired position of %s" % (self.descr,),
            helpURL = HelpURL,
        )

    def getCmd(self):
        """Return the command string to command the current user setting, or None if already there
        """
        if self.currWdg.isCurrent():
            return None
        return "%s %s" % (self.label, self.currWdg.getString())

    def statusCallback(self, valueList, isCurrent, keyVar=None):
        """Status updated
        """
        isMoving = valueList[0]
        currPos = valueList[1]
        moveDuration = valueList[3]
        self.currWdg.set(currPos, isCurrent=isCurrent)
        self.userWdg.setDefault(currPos, isCurrent=isCurrent)
        if isMoving and moveDuration > 0:
            self.progressBar.start(value=moveDuration, newMax=moveDuration)
            self.progressBar.grid()
        else:
            self.progressBar.grid_remove()
            self.userWdg.setDefault(currPos, isCurrent=isCurrent, doCheck=False)


class FilterControls(StageControls):
    def statusCallback(self, valueList, isCurrent, keyVar=None):
        """Status updated
        """
        isMoving = valueList[0]
        currPos = valueList[3]
        moveDuration = valueList[7]
        self.currWdg.set(currPos, isCurrent=isCurrent)
        self.userWdg.setDefault(currPos, isCurrent=isCurrent, doCheck=False)
        if isMoving and moveDuration > 0:
            self.progressBar.start(value=moveDuration, newMax=moveDuration)
            self.progressBar.grid()
        else:
            self.progressBar.grid_remove()
            self.userWdg.setDefault(currPos, isCurrent=isCurrent, doCheck=False)


class OtherDialog(RO.Wdg.InputDialog.ModalDialogBase):
    """Dialog box to enter a custom value into an OptionMenu
    """
    def __init__(self, master, currValue, descr):
        self._currValue = currValue
        self._descr = descr.title()
        RO.Wdg.InputDialog.ModalDialogBase.__init__(self, master=master, title=self._descr)

    def body(self, master):
        RO.Wdg.StrLabel(master=master, text="%s Position" % (self._descr,)).grid(row=0, column=0, columnspan=2)
        RO.Wdg.StrLabel(master=master, text="Current").grid(row=1, column=0, sticky="e")
        RO.Wdg.StrLabel(master=master, text=str(self._currValue)).grid(row=1, column=1, sticky="e")
        RO.Wdg.StrLabel(master=master, text="New").grid(row=2, column=0, sticky="e")
        self.entryWdg = RO.Wdg.FloatEntry(master)
        self.entryWdg.grid(row=2, column=1, sticky="e")
        return self.entryWdg # return the item that gets initial focus

    def setResult(self):
        self.result = self.entryWdg.getNumOrNone()


if __name__ == '__main__':
    import TestData
    root = TestData.tuiModel.tkRoot
    stateTracker = RO.Wdg.StateTracker(logFunc=TestData.tuiModel.logFunc)
    
    testFrame = StatusConfigInputWdg(root, stateTracker=stateTracker)
    testFrame.pack()
    
    TestData.start()
    
    testFrame.restoreDefault()

    def printCmds():
        try:
            cmdList = testFrame.getStringList()
        except ValueError as e:
            print "Command error:", e
            return
        if cmdList:
            print "Commands:"
            for cmd in cmdList:
                print cmd
        else:
            print "(no commands)"
    
    bf = Tkinter.Frame(root)
    cfgWdg = RO.Wdg.Checkbutton(bf, text="Config", defValue=True)
    cfgWdg.pack(side="left")
    Tkinter.Button(bf, text='Cmds', command=printCmds).pack(side='left')
    Tkinter.Button(bf, text='Current', command=testFrame.restoreDefault).pack(side='left')
    Tkinter.Button(bf, text='Demo', command=TestData.animate).pack(side='left')
    bf.pack()

    testFrame.gridder.addShowHideControl(testFrame.ConfigCat, cfgWdg)

    root.mainloop()
