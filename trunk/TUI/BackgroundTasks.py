#!/usr/bin/env python
"""
Handle background (invisible) tasks for the telescope UI

To do: put up a log window so the intentional error in the test case can be seen

History:
2003-02-27 ROwen    Error messages now go to the log, not stderr.
2003-03-05 ROwen    Modified to use simplified KeyVariables.
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-06-18 ROwen    Modified to test for StandardError instead of Exception
2003-06-25 ROwen    Modified to handle message data as a dict
2004-02-05 ROwen    Modified to use improved KeyDispatcher.logMsg.
2005-06-08 ROwen    Changed BackgroundKwds to a new style class.
2005-06-16 ROwen    Modified to use improved KeyDispatcher.logMsg.
2005-09-28 ROwen    Modified checkTAI to use standard exception handling template.
2006-10-25 ROwen    Modified to use TUIModel and so not need the dispatcher keyword.
                    Modified to log errors using tuiModel.logMsg.
2007-07-25 ROwen    Modified to use time from the TCC model.
                    Modified to not test the clock unless UTCMinusTAI set
                    (but TUI now gets that using getKeys so it normally will
                    see UTCMinusTAI before it sees the current TAI).
2010-07-21 ROwen    Added support for detecting sleep and failed connections.
2010-10-27 ROwen    Fixed "no data seen" message to report correct time interval.
2011-06-16 ROwen    Ditched obsolete "except (SystemExit, KeyboardInterrupt): raise" code
2011-06-17 ROwen    Changed "type" to "msgType" in parsed message dictionaries (in test code only).
2012-07-18 ROwen    Modified to user RO.Comm.Generic.Timer.
2012-08-01 ROwen    Updated for RO.Comm.TCPConnection 3.0.
"""
import sys
import time
import RO.CnvUtil
import RO.Constants
import RO.PhysConst
import RO.Astro.Tm
import RO.KeyVariable
from RO.Comm.Generic import Timer
import RO.TkUtil
import TUI.PlaySound
import TUI.TUIModel
import TUI.TCC.TCCModel

class BackgroundKwds(object):
    """Processes various keywords that are handled in the background.
    
    Also verify that we're getting data from the hub (also detects computer sleep)
    and try to refresh variables if there is a problem.
    """
    def __init__(self,
        maxTimeErr = 10.0,
        checkConnInterval = 5.0,
        maxEntryAge = 60.0,
    ):
        """Create BackgroundKwds
        
        Inputs:
        - maxTimeErr: maximum clock error (sec) before a warning is printed
        - checkConnInterval: interval (sec) at which to check connection
        - maxEntryAge: maximum age of log entry (sec)
        """
        self.maxTimeErr = float(maxTimeErr)
        self.checkConnInterval = float(checkConnInterval)
        self.maxEntryAge = float(maxEntryAge)

        self.tuiModel = TUI.TUIModel.getModel()
        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.connection = self.tuiModel.getConnection()
        self.dispatcher = self.tuiModel.dispatcher
        self.didSetUTCMinusTAI = False
        self.checkConnTimer = Timer()

        self.tccModel.utcMinusTAI.addCallback(self.setUTCMinusTAI, callNow=False)
        self.tccModel.tai.addCallback(self.checkTAI, callNow=False)
    
        self.connection.addStateCallback(self.connCallback, callNow=True)

    def connCallback(self, conn):
        """Called when connection changes state

        When connected check the connection regularly,
        when not, don't
        """
        if conn.isConnected:
            self.checkConnTimer.start(self.checkConnInterval, self.checkConnection)
        else:
            self.checkConnTimer.cancel()
    
    def checkConnection(self):
        """Check for aliveness of connection by looking at the time of the last hub message
        """
        doQueue = True
        try:
            entryAge = time.time() - self.dispatcher.readUnixTime
            if entryAge > self.maxEntryAge:
                self.tuiModel.logMsg(
                    "No data seen in %s seconds; testing the connection" % (self.maxEntryAge,),
                    severity = RO.Constants.sevWarning)
                cmdVar = RO.KeyVariable.CmdVar(
                    actor = "hub",
                    cmdStr = "version",
                    timeLim = 5.0,
                    dispatcher = self.dispatcher,
                    callFunc=self.checkCmdCallback,
                )
                doQueue = False
        finally:
            if doQueue:
                self.checkConnTimer.start(self.checkConnInterval, self.checkConnection)

    def checkCmdCallback(self, msgType, msgDict, cmdVar):
        if not cmdVar.isDone():
            return
        doQueue = True
        try:
            if cmdVar.didFail():
                self.connection.disconnect(isOK = False, reason="Connection is dead")
                doQueue = False
                TUI.PlaySound.cmdFailed()
            else:
                self.dispatcher.refreshAllVar()
        finally:
            if doQueue:
                self.checkConnTimer.start(self.checkConnInterval, self.checkConnection)
        
    def setUTCMinusTAI(self, valueList, isCurrent=1, keyVar=None):
        """Updates UTC-TAI in RO.Astro.Tm
        """
        if isCurrent and valueList[0] != None:
            RO.Astro.Tm.setUTCMinusTAI(valueList[0])
            self.didSetUTCMinusTAI = True

    def checkTAI(self, valueList, isCurrent=1, keyVar=None):
        """Updates azimuth, altitude, zenith distance and airmass
        valueList values are: az, alt, rot
        """
        if not isCurrent or not self.didSetUTCMinusTAI:
            return

        try:
            if valueList[0] != None:
                timeErr = (RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay) - valueList[0]
                
                if abs(timeErr) > self.maxTimeErr:
                    self.tuiModel.logMsg(
                        "Your clock appears to be off; time error = %.1f" % (timeErr,),
                        severity = RO.Constants.sevError,
                    )
        except Exception, e:
            self.tuiModel.logMsg(
                "TAI time keyword seen but clock check failed; error=%s" % (e,),
                severity = RO.Constants.sevError,
            )
                

if __name__ == "__main__":
    import TUI.TUIModel
    import RO.Wdg
    root = RO.Wdg.PythonTk()
        
    kd = TUI.TUIModel.getModel(True).dispatcher

    bkgnd = BackgroundKwds()

    msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "msgType":":"}
    
    print "Setting TAI and UTC_TAI correctly; this should work silently."
    dataDict = {
        "UTC_TAI": (-33,), # a reasonable value
    }
    msgDict["data"] = dataDict
    kd.dispatch(msgDict)

    dataDict = {
        "TAI": (RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay,),
    }
    msgDict["data"] = dataDict
    kd.dispatch(msgDict)
    
    # now generate an intentional error
    print "Setting TAI incorrectly; this would log an error if we had a log window up:"
    dataDict = {
        "TAI": ((RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay) + 999.0,),
    }
    msgDict["data"] = dataDict

    kd.dispatch(msgDict)

    root.mainloop()
