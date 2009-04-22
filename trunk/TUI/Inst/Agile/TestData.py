#!/usr/bin/env python
import RO.Alg
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()
actor = "agile"

MainDataSet = (
    "cameraConnState=Connected, ''",
    'filter_names="Open", "MK_J", "MK_H", "MK_K", "MK_L", "MK_M"',
    "filter_done=Open",
    "window=1, 1, 1024, 1024",
    "overscan=27, 0",
    "bin=2",
    "ccdTempLimits=1.5, 1.5, 10, 10",
    "ccdTemp=-40, normal",
    "ccdSetTemp=-40, normal",
    "gpsSynced=T",
    "ntpStatus=T, 'galileo.apo.nms', 1",
)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
    ("filter_ttc=3",),
    ("gpsSynced=F",),
    ("ntpStatus=F, '?', ?",),
    ("gpsSynced=T",),
    ("ntpStatus=T, '?', ?",),
    ("ntpStatus=T, 'galileo.apo.nmsu', ?",),
    ("ntpStatus=T, 'galileo.apo.nmsu', 1",),
    ("ccdTemp=-5, veryHigh",),
    ("ccdTemp=-35, high",),
    ("ccdTemp=-45, low",),
    ("ccdTemp=-65, veryLow",),
    ("ccdTemp=-40, normal",),
    ("filter_done=MK_J",),
    ("window=4, 5, 1001, 1002",),
)

MsgPrefix = "%s %s %s %s " % (cmdr, 11, actor, ":")

def dispatch(dataSet=None):
    """Dispatch a set of data, i.e. a list of keyword, value tuples"""
    if dataSet == None:
        dataSet = MainDataSet
    msgStr = MsgPrefix + "; ".join(dataSet)
    print "Dispatching data:", msgStr
    dispatcher.doRead(None, msgStr)
    
def animate(dataIter=None):
    if dataIter == None:
        dataIter = iter(AnimDataSet)
    try:
        data = dataIter.next()
    except StopIteration:
        return
    dispatch(data)
    
    tuiModel.tkRoot.after(1500, animate, dataIter)
