#!/usr/bin/env python
"""Configuration input panel for GIFS.

History:
2014-02-03 ROwen
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import TUI.TUIModel
import GIFSModel

_DataWidth = 8  # width of data columns
_EnvWidth = 6 # width of environment value columns

class StageControls(object):
    """A set of widgets that controls one generic GIFS motorized stage
    """
    def __init__(self, master, row, label, configKey, statusKey, descr=None):
        """Construct the widgets, grid them and wire them up

        @param[in] master: master widget into which to grid widgets
        @param[in] row: row in which to grid widgets (starting at column 0)
        @param[in] label: label for this device
        @param[in] configKey: configuration keyword variable; None if none
        @param[in] statusKey: status keyword variable
        @param[in] descr: brief description, for help strings; if None then label.lower()
        """
        self.master = master
        self.row = row
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
            master = self.master,
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

        col=0
        nameWdg = RO.Wdg.StrLabel(master=self.master, text=self.label)
        nameWdg.grid(row=self.row, column=col)
        col += 1

        self.currWdg = RO.Wdg.StrLabel(
            master = self.master,
            helpText = "current position of %s" % (self.descr,),
        )
        self.currWdg.grid(row=self.row, column=col)
        col += 1

        self.userWdg = self._makeUserWdg()
        self.userWdg.grid(row=self.row, column=col)
        col += 1

        self.progressBar = RO.Wdg.TimeBar(master = self.master)
        self.progressBar.grid(row=self.row, column=col)
        self.progressBar.grid_remove()
        col += 1

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
            items = valueList,
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
        if isMoving:
            self.progressBar.start(value=moveDuration)
            self.progressBar.grid()
        else:
            self.progressBar.grid_remove()

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.label)


class CalMirrorControls(StageControls):
    def __init__(self, master, row, statusKey):
        StageControls.__init__(self,
            master = master,
            row = row,
            label = "Cal Mirror",
            configKey = None,
            statusKey = statusKey,
            descr = "calibration mirror",
        )

    def _makeUserWdg(self):
        """Make the user widget and return it
        """
        return RO.Wdg.Checkbutton(
            master = self.master,
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
    def __init__(self, master, row, filterPosKey, statusKey):
        self.filterNameDict = {}
        StageControls.__init__(self,
            master = master,
            row = row,
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

        nameList = [self.filterNameDict[i] for i in sorted(self.filterNameDict.keys())]
        self.userWdg.setItems(nameList)

    def statusCallback(self, valueList, isCurrent, keyVar=None):
        """Status updated
        """
        currPos = valueList[3]
        self.currWdg.set(currPos, isCurrent=isCurrent)
        self.userWdg.setDefault(currPos, isCurrent=isCurrent, doCheck=False)
        self.progressBar.grid_remove()


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
        """
        RO.Wdg.InputContFrame.__init__(self, master, stateTracker=stateTracker, **kargs)
        self.model = GIFSModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()
        
        self.settingCurrWin = False

        row = 0

        # (self, master, row, label, configKey, statusKey, descr=None):
        self.magnifier = StageControls(
            master = self,
            row = row,
            label = "Magnifier",
            configKey = self.model.magnifierConfig,
            statusKey = self.model.magnifierStatus,
        )
        row += 1
    
        self.lenslets = StageControls(
            master = self,
            row = row,
            label = "Lenslets",
            configKey = self.model.lensletsConfig,
            statusKey = self.model.lensletsStatus,
            descr = "lenslet array"
        )
        row += 1

        self.calMirror = CalMirrorControls(
            master = self,
            row = row,
            statusKey = self.model.calMirrorStatus,
        )
        row += 1

        self.filter = FilterControls(
            master = self,
            row = row,
            filterPosKey = self.model.filterPos,
            statusKey = self.model.filterStatus,
        )
        row += 1

        self.collimator = StageControls(
            master = self,
            row = row,
            label = "Collimator",
            configKey = self.model.collimatorConfig,
            statusKey = self.model.collimatorStatus,
        )
        row += 1
        self.disperser = StageControls(
            master = self,
            row = row,
            label = "Disperser",
            configKey = self.model.disperserConfig,
            statusKey = self.model.disperserStatus,
        )
        row += 1

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
        
        # def repaint(evt):
        #     self.restoreDefault()
        # self.bind('<Map>', repaint)


if __name__ == '__main__':
    import TestData
    root = TestData.tuiModel.tkRoot
    stateTracker = RO.Wdg.StateTracker(logFunc = TestData.tuiModel.logFunc)
    
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
