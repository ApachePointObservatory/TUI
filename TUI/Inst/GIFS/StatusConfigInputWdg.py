#!/usr/bin/env python
"""Configuration input panel for GIFS.

History:
2014-02-05 ROwen
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import TUI.TUIModel
import GIFSModel

_DataWidth = 8  # width of data columns
_EnvWidth = 6 # width of environment value columns

_DefaultConfig = dict(
)

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
    InstName = "GIFS"
    HelpPrefix = 'Instruments/%s/%sWin.html#' % (InstName, InstName)

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
            filterPosKey = self.model.filterPos,
            statusKey = self.model.filterStatus,
        )

        self.collimator = StageControls(
            gridder = self.gridder,
            label = "Collimator",
            configKey = self.model.collimatorConfig,
            statusKey = self.model.collimatorStatus,
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

        eqFmtFunc = RO.InputCont.BasicFmt(
            nameSep="=",
        )

        # set up the input container set
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = 'magnifier move',
                    wdgs = self.magnifier.userWdg,
                    formatFunc = eqFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = 'lenslets move',
                    wdgs = self.lenslets.userWdg,
                    formatFunc = eqFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = 'calmirror ',
                    wdgs = self.calMirror.userWdg,
                ),
                RO.InputCont.WdgCont (
                    name = 'filter move',
                    wdgs = self.filter.userWdg,
                    formatFunc = eqFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = 'collimator move',
                    wdgs = self.collimator.userWdg,
                    formatFunc = eqFmtFunc,
                ),
                RO.InputCont.WdgCont (
                    name = 'disperser move',
                    wdgs = self.disperser.userWdg,
                    formatFunc = eqFmtFunc,
                ),
            ],
        )
        
        self.configWdg = RO.Wdg.InputContConfigWdg(
            master = self,
            sysName = "%sConfig" % (self.InstName,),
            userConfigsDict = self.tuiModel.userConfigsDict,
            inputCont = self.inputCont,
            text = "Configs",
        )
        self.gridder.gridWdg(
            cfgWdg = self.configWdg,
        )

        self.gridder.allGridded()
        
        def repaint(evt):
            self.restoreDefault()
        self.bind("<Map>", repaint)


class StageControls(object):
    """A set of widgets that controls one generic GIFS motorized stage
    """
    def __init__(self, gridder, label, configKey, statusKey, descr=None):
        """Construct the widgets, grid them and wire them up

        @param[in] gridder: gridder to use to grid widgets
        @param[in] label: label for this device
        @param[in] configKey: configuration keyword variable; None if none
        @param[in] statusKey: status keyword variable
        @param[in] descr: brief description, for help strings; if None then label.lower()
        """
        self.gridder = gridder
        self.label = label
        self.configKey = configKey
        self.statusKey = statusKey
        self.descr = descr if descr is not None else label.lower()
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
            helpText = "desired position of %s" % (self.descr,)
        )

    def _makeWdg(self):
        """Make currWdg and userWdg
        """
        if hasattr(self, "currWdg"):
            raise RuntimeError("widgets already exist")

        self.currWdg = RO.Wdg.StrLabel(
            master = self.gridder.master,
            helpText = "current position of %s" % (self.descr,),
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

    def configCallback(self, valueList, isCurrent, keyVar=None):
        """Config updated
        """
        self.userWdg.setItems(
            items = sorted(valueList),
            isCurrent = isCurrent,
            checkCurrent = True,
            checkDef = False,
        )

    def statusCallback(self, valueList, isCurrent, keyVar=None):
        """Status updated
        """
        isMoving = valueList[0]
        currPos = valueList[1]
        moveDuration = valueList[3]
        self.currWdg.set(currPos, isCurrent=isCurrent)
        self.userWdg.setDefault(currPos, isCurrent=isCurrent, doCheck=False)
        if isMoving and moveDuration > 0:
            self.progressBar.start(value=moveDuration, newMax=moveDuration)
            self.progressBar.grid()
        else:
            self.progressBar.grid_remove()

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
        currPos = valueList[0]
        self.currWdg.set(currPos, isCurrent=isCurrent)
        self.userWdg.setDefault(currPos, isCurrent=isCurrent)
        self.progressBar.grid_remove()


class FilterControls(StageControls):
    def __init__(self, gridder, filterPosKey, statusKey):
        self.filterNameDict = {}
        StageControls.__init__(self,
            gridder = gridder,
            label = "Filter Wheel",
            configKey = None,
            statusKey = statusKey,
        )
        self.filterPosKey = filterPosKey
        filterPosKey.addCallback(self.filterPosCallback)

    def filterPosCallback(self, valueList, isCurrent, keyVar=None):
        """new filterPos data
        """
        if not isCurrent:
            return

        slot = valueList[0]
        name = valueList[1]
        self.filterNameDict[slot] = name

        nameList = sorted(self.filterNameDict.itervalues())
        self.userWdg.setItems(nameList)

    def statusCallback(self, valueList, isCurrent, keyVar=None):
        """Status updated
        """
        currPos = valueList[3]
        self.currWdg.set(currPos, isCurrent=isCurrent)
        self.userWdg.setDefault(currPos, isCurrent=isCurrent, doCheck=False)
        self.progressBar.grid_remove()


if __name__ == '__main__':
    import TestData
    root = TestData.tuiModel.tkRoot
    stateTracker = RO.Wdg.StateTracker(logFunc=TestData.tuiModel.logFunc)
    
    testFrame = StatusConfigInputWdg(root, stateTracker=stateTracker)
    testFrame.pack()
    
    testFrame.restoreDefault()

    def printCmds():
        try:
            cmdList = testFrame.getStringList()
        except ValueError, e:
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
    
    TestData.start()

    root.mainloop()
