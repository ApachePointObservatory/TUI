#!/usr/bin/env python
"""Data for testing various DIS widgets

History:
2011-07-20 ROwen
"""
import RO.Alg
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataSet = (
    ("shutter", ("closed",)),
    ("ccdState", ("ok",)),
    ("name", ("dtest030319.",)),
    ("number", (1,)),
    ("places", (4,)),
    ("path", ("/export/images",)),
    ("basename", ("/export/images/dtest030319.0001",)),
)
MainDataSet = RO.Alg.OrderedDict(MainDataSet)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
    {}
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":"shack", "msgType":":"}
MainMsgDict = {"data":MainDataSet}.update(BaseMsgDict)

def dispatch(dataSet=None):
    """Dispatch a set of data, i.e. a list of keyword, value tuples"""
    if dataSet == None:
        dataSet = MainDataSet
    print "Dispatching data:", dataSet
    msgDict = {"data":dataSet}
    msgDict.update(BaseMsgDict)
    dispatcher.dispatch(msgDict)
    
def animate(dataIter=None):
    if dataIter == None:
        dataIter = iter(AnimDataSet)
    try:
        data = dataIter.next()
    except StopIteration:
        return
    dispatch(data)
    
    tuiModel.tkRoot.after(1500, animate, dataIter)
