#!/usr/bin/env python
"""Configuration input panel for Agile.

To do:
- Add filter wheel support.
- Support downloading every Nth image, or at least skipping images if we get behind.

History:
2008-10-24 ROwen    preliminary adaptation from DIS
2008-11-06 ROwen    Removed unused detector controls; the rest is not yet functional
2008-11-07 ROwen    Implemented temperature display. Still need functional filter control.
2008-11-10 ROwen    Commented out nonfunctional filter code.
                    Set minimum temperature width so no info shows up properly.
                    Call temperature callbacks right away.
2009-04-17 ROwen    Added full evironmental display
2009-04-20 ROwen    Commented out a debug print statement.
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import TUI.Base.StateSet
import TUI.TUIModel
import AgileModel

_DataWidth = 8  # width of data columns
_EnvWidth = 6 # width of environment value columns

DevCamera = "Camera"
DevCCDTemp = "CCD Temp"
DevCCDSetTemp = "CCD Set Temp"
DevGPSSynced = "GPS Synced"
DevNTPStatus = "NTP Status"
DevNames = (DevCamera, DevCCDTemp, DevCCDSetTemp, DevGPSSynced, DevNTPStatus)

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
    InstName = "Agile"
    HelpPrefix = "Instruments/%sWin.html#" % (InstName,)

    # category names
    ConfigCat = RO.Wdg.StatusConfigGridder.ConfigCat
    EnvironCat = 'temp'

    def __init__(self,
        master,
    **kargs):
        """Create a new widget to show status for and configure Agile
        """
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        self.model = AgileModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()
        
        self.environStateSet = TUI.Base.StateSet.StateSet(DevNames, callFunc=self._updEnvironStateSet)
        
        self.settingCurrWin = False
    
        gr = RO.Wdg.StatusConfigGridder(
            master = self,
            sticky = "w",
            numStatusCols = 3,
        )
        self.gridder = gr
        
        # filter (plus blank label to maintain minimum width)
        blankLabel = Tkinter.Label(self, width=_DataWidth)

        self.filterCurrWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "current filter",
            helpURL = self.HelpPrefix + "Filter",
        )
        
        self.filterTimerWdg = RO.Wdg.TimeBar(master = self, valueFormat = "%3.0f")
        
        self.filterUserWdg = RO.Wdg.OptionMenu(
            master = self,
            items=[],
            helpText = "requested filter",
            helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
            isCurrent = False,
        )

#         filtRow = gr.getNextRow()
#         # reserve _DataWidth width
#         blankLabel.grid(
#             row = filtRow,
#             column = 1,
#             columnspan = 2,
#         )
#         gr.gridWdg (
#             label = 'Filter',
#             dataWdg = self.filterCurrWdg,
#             units = None,
#             cfgWdg = self.filterUserWdg,
#             colSpan = 2,
#         )
#         self.filterTimerWdg.grid(
#             row = filtRow,
#             column = 1,
#             columnspan = 2,
#             sticky = "w",
#         )
        self._showFilterTimer(False)

#         self.model.filter.addIndexedCallback(self._updFilter)
#         self.model.filterTime.addIndexedCallback(self._updFilterTime)

        # Temperature State information
        
        self.ccdTempStateDict = {
            None: (None, RO.Constants.sevNormal),
            "normal": ("", RO.Constants.sevNormal),
            "low": ("Low", RO.Constants.sevWarning),
            "high": ("High", RO.Constants.sevWarning),
            "verylow": ("Very Low", RO.Constants.sevError),
            "veryhigh": ("Very High", RO.Constants.sevError),
        }
        
        # Environment
        
        self.environShowHideWdg = RO.Wdg.Checkbutton(
            master = self,
            text = "Environ",
            indicatoron = False,
            helpText = "Show/hide environment details",
            helpURL = self.HelpPrefix + "Environment",
        )
        
        self.environSummaryWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Environment summary",
            helpURL = self.HelpPrefix + "Environment",
        )

        gr.gridWdg (
            label = self.environShowHideWdg,
            dataWdg = self.environSummaryWdg,
            colSpan=3,
            numStatusCols = None,
        )

        # Camera connected
        self.cameraConnStateWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "Camera connection state",
            helpURL = self.HelpPrefix + "CameraConn",
        )
        gr.gridWdg("Camera", self.cameraConnStateWdg, cat = self.EnvironCat)
        
        self.ccdTempWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Current CCD Temp (C)",
            helpURL = self.HelpPrefix + "CCDTemp",
        )
        
        gr.gridWdg (
            label = DevCCDTemp,
            dataWdg = self.ccdTempWdg,
            cat = self.EnvironCat,
        )
        
        # CCD Set Temperature
        
        self.ccdSetTempWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Desired CCD Temp (C)",
            helpURL = self.HelpPrefix + "CCDTemp",
        )

        gr.gridWdg (
            label = DevCCDSetTemp,
            dataWdg = self.ccdSetTempWdg,
            cat = self.EnvironCat,
        )
        
        # CCD Temperature Limits
        
        self.ccdTempLimitsFrame = Tkinter.Frame(self)
        self.ccdTempLimitsWdgSet = []
        for col, limitName in enumerate(("Low", "High", "Very Low", "Very High")):
            ccdTempLimitWdg = RO.Wdg.FloatLabel(
                self.ccdTempLimitsFrame,
                precision = 1,
                width = _EnvWidth,
                helpText = "Error limit for %s CCD temp." % (limitName.lower(),)
            )
            ccdTempLimitWdg.grid(row=0, column=col)
            self.ccdTempLimitsWdgSet.append(ccdTempLimitWdg)
        
        gr.gridWdg(
            label = "CCD Temp Limits",
            dataWdg = self.ccdTempLimitsFrame,
            colSpan = 10,
            numStatusCols = None,
            cat = self.EnvironCat,
        )
        
        self.gpsSyncedWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "Is clock card synched to the GPS clock?",
            helpURL = self.HelpPrefix + "GPSSynced",
        )
       
        gr.gridWdg(
            label = DevGPSSynced,
            dataWdg = self.gpsSyncedWdg,
            cat = self.EnvironCat,
         )
        
        self.ntpStatusFrame = Tkinter.Frame(self)
        self.ntpStatusWdgSet = []
        for col, helpStr in enumerate(("Is NTP client running?", "NTP server", "Stratum of NTP server")):
            ntpStatusWdg = RO.Wdg.StrLabel(
                self.ntpStatusFrame,
                helpText = helpStr,
            )
            ntpStatusWdg.grid(row=0, column=col)
            self.ntpStatusWdgSet.append(ntpStatusWdg)

        gr.gridWdg(
            label = DevNTPStatus,
            dataWdg = self.ntpStatusFrame,
            colSpan = 10,
            numStatusCols = None,
            cat = self.EnvironCat,
         )
            
        gr.allGridded()
        
        self.gpsSyncedDict = {
            True: (RO.Constants.sevNormal, "Yes"),
            False: (RO.Constants.sevError, "No"),
            None: (RO.Constants.sevWarning, "?"),
        }
        
        self.ntpRunningDict = {
            True: "Running",
            False: "NotRunning",
            None: "?",
        }

        # add callbacks that deal with multiple widgets
#         self.model.filterNames.addCallback(self._updFilterNames)
        self.environShowHideWdg.addCallback(self._doShowHide, callNow = False)
        self.model.cameraConnState.addCallback(self._updCameraConnState, callNow = True)
        self.model.ccdTemp.addCallback(self._updCCDTemp, callNow = True)
        self.model.ccdSetTemp.addCallback(self._updCCDSetTemp, callNow = True)
        self.model.ccdTempLimits.addCallback(self._updCCDTempLimits, callNow = True)
        self.model.gpsSynced.addCallback(self._updGPSSynced, callNow=True)
        self.model.ntpStatus.addCallback(self._updNTPStatus, callNow=True)
        self._doShowHide()
        
        eqFmtFunc = RO.InputCont.BasicFmt(
            nameSep="=",
        )

        # set up the input container set
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = 'filters set',
                    wdgs = self.filterUserWdg,
                    formatFunc = eqFmtFunc,
                ),
            ],
        )
        
        def repaint(evt):
            self.restoreDefault()
        self.bind('<Map>', repaint)

    def _doShowHide(self, wdg=None):
        showTemps = self.environShowHideWdg.getBool()
        argDict = {self.EnvironCat: showTemps}
        self.gridder.showHideWdg (**argDict)
    
    def _showFilterTimer(self, doShow):
        """Show or hide the filter timer
        (and thus hide or show the current filter name).
        """
        if doShow:
            self.filterTimerWdg.grid()
            self.filterCurrWdg.grid_remove()
        else:
            self.filterCurrWdg.grid()
            self.filterTimerWdg.grid_remove()
            
    def _updCameraConnState(self, cameraConnState, isCurrent, keyVar=None):
        stateStr = cameraConnState[0]
        descrStr = cameraConnState[1]
        if not stateStr:
            stateStr = "?"
        isConnected = stateStr.lower() == "connected"
        if isConnected:
            severity = RO.Constants.sevNormal
        else:
            severity = RO.Constants.sevWarning
        self.cameraConnStateWdg.set(stateStr, isCurrent=isCurrent, severity=severity)
        self.environStateSet.setState(DevCamera, isCurrent=isCurrent, severity=severity, stateStr=stateStr)
    
    def _updCCDTemp(self, dataList, isCurrent, keyVar=None):
        #print "_updCCDTemp(dataList=%s, isCurrent=%s)" % (dataList, isCurrent)
        ccdTemp, tempStatus = dataList[0:2]
        if ccdTemp == None:
            stateStr = "?"
        else:
            stateStr = "%0.1f" % (ccdTemp,)
        if tempStatus != None:
            tempStatus = tempStatus.lower()
        dispStr, severity = self.ccdTempStateDict.get(tempStatus, (tempStatus, RO.Constants.sevWarning))
        if dispStr != None:
            stateStr = "%s %s" % (stateStr, dispStr)
        self.ccdTempWdg.set(stateStr, isCurrent=isCurrent, severity=severity)
        if not isCurrent or severity != RO.Constants.sevNormal:
            self.environStateSet.setState(DevCCDTemp, isCurrent = isCurrent, severity = severity, stateStr=stateStr)
        else:
            self.environStateSet.clearState(DevCCDTemp)
        
    
    def _updCCDSetTemp(self, dataList, isCurrent, keyVar=None):
        #print "_updCCDSetTemp(dataList=%s, isCurrent=%s)" % (dataList, isCurrent)
        ccdSetTemp, tempStatus = dataList[0:2]
        if ccdSetTemp == None:
            stateStr = "?"
        else:
            stateStr = "%0.1f" % (ccdSetTemp,)
        if tempStatus != None:
            tempStatus = tempStatus.lower()
        dispStr, severity = self.ccdTempStateDict.get(tempStatus, (tempStatus, RO.Constants.sevWarning))
        if dispStr != None:
            stateStr = "%s %s" % (stateStr, dispStr)
        self.ccdSetTempWdg.set(stateStr, isCurrent=isCurrent, severity=severity)
        if not isCurrent or severity != RO.Constants.sevNormal:
            self.environStateSet.setState(DevCCDSetTemp, isCurrent = isCurrent, severity = severity, stateStr=stateStr)
        else:
            self.environStateSet.clearState(DevCCDSetTemp)
    
    def _updCCDTempLimits(self, ccdTempLimits, isCurrent, keyVar=None):
        #print "_updCCDTempLimits(ccdTempLimits=%s, isCurrent=%s)" % (ccdTempLimits, isCurrent)
        for ind, wdg in enumerate(self.ccdTempLimitsWdgSet):
            tempLimit = ccdTempLimits[ind]
            if tempLimit == None:
                wdg.grid_remove()
            else:
                tempLimit = abs(tempLimit)
                if ind % 2 == 0: # limits 0 and 2 are negative
                    tempLimit = -tempLimit
                wdg.grid()
                wdg.set(tempLimit)
    
    def _updGPSSynced(self, dataList, isCurrent, keyVar=None):
        gpsSynced = dataList[0]
        severity, stateStr = self.gpsSyncedDict[dataList[0]]
        self.gpsSyncedWdg.set(stateStr, isCurrent=isCurrent, severity=severity)
        if severity == RO.Constants.sevNormal and isCurrent:
            self.environStateSet.clearState(DevGPSSynced)
        else:
            self.environStateSet.setState(DevGPSSynced, isCurrent=isCurrent, severity=severity, stateStr=stateStr)
         
    
    def _updNTPStatus(self, dataList, isCurrent, keyVar=None):
        isRunning, server, stratum = dataList[0:3]
        severity = RO.Constants.sevNormal
        if isRunning == False:
            severity = RO.Constants.sevError
        elif (isRunning == None) or (server == "?") or (stratum == None):
            severity = RO.Constants.sevWarning
        isRunningStr = self.ntpRunningDict[isRunning]
        if server == None:
            serverStr = "?"
        else:
            serverStr = server.split(".")[0]
        stratumStr = stratum if stratum != None else "?"
        self.ntpStatusWdgSet[0].set(isRunningStr, isCurrent=isCurrent, severity=severity)
        self.ntpStatusWdgSet[1].set(serverStr, isCurrent=isCurrent, severity=severity)
        self.ntpStatusWdgSet[2].set(stratumStr, isCurrent=isCurrent, severity=severity)
        stateStr = "%s %s %s" % (isRunningStr, serverStr, stratumStr)
        if severity == RO.Constants.sevNormal and isCurrent:
            self.environStateSet.clearState(DevNTPStatus)
        else:
            self.environStateSet.setState(DevNTPStatus, isCurrent=isCurrent, severity=severity, stateStr=stateStr)

    def _updEnvironStateSet(self, *args):
        """Environmental state set updated"""
        state = self.environStateSet.getFirstState()
        #print "_updEnvironStateSet; first state=", state
        if not state:
            self.environSummaryWdg.set("OK", isCurrent=True, severity=RO.Constants.sevNormal)
        else:
             summaryStr = "%s: %s" % (state.name, state.stateStr)
             self.environSummaryWdg.set(summaryStr, isCurrent=state.isCurrent, severity=state.severity)

    def _updFilter(self, filterName, isCurrent, keyVar=None):
        self._showFilterTimer(False)
        if filterName != None and filterName.lower() == "unknown":
            severity = RO.Constants.sevError
            self.filterUserWdg.setDefault(
                None,
                isCurrent = isCurrent,
            )
        else:
            severity = RO.Constants.sevNormal
            self.filterUserWdg.setDefault(
                filterName,
                isCurrent = isCurrent,
            )

        self.filterCurrWdg.set(
            filterName,
            isCurrent = isCurrent,
            severity = severity,
        )

    def _updFilterNames(self, filterNames, isCurrent, keyVar=None):
        if not filterNames or None in filterNames:
            return

        self.filterUserWdg.setItems(filterNames, isCurrent=isCurrent)
        
        # set width of slit and filter widgets
        # setting both helps keep the widget from changing size
        # if one is replaced by a timer.
        maxNameLen = max([len(fn) for fn in filterNames])
        maxNameLen = max(maxNameLen, 3) # room for "Out" for slitOPath
        self.filterCurrWdg["width"] = maxNameLen

    def _updFilterTime(self, filterTime, isCurrent, keyVar=None):
        if filterTime == None or not isCurrent:
            self._showFilterTimer(False)
            return
        
        self._showFilterTimer(True)
        self.filterTimerWdg.start(filterTime, newMax = filterTime)
    

if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
        
    testFrame = StatusConfigInputWdg (root)
    testFrame.pack()
    
    TestData.dispatch()
    
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
    
    testFrame.gridder.addShowHideControl(testFrame.ConfigCat, cfgWdg)
    
    root.mainloop()
