#!/usr/bin/env python
"""Data for testing various DIS widgets

History:
2005-07-21 ROwen    Bug fix: was not dispatching MainDataSet in order
                    (because it was specified as a normal non-ordered dict).
2008-04-24 ROwen    Bug fix: had too few filter names.
"""
import RO.Alg
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataSet = (
    ("filterNames", ("SDSS u'","SDSS g'","SDSS r'","SDSS i'","SDSS z'","Hodge 6629",)),
    ("filterID", (1,)),
    ("filterName", ("Hodge 6629",)),
    ("shutter", ("closed",)),
    ("ccdState", ("ok",)),
    ("ccdBin", (2,2,)),
    ("ccdWindow", (1,1,1024,514,)),
    ("ccdUBWindow", (1,1,2048,1028,)),
    ("ccdOverscan", (50,50,)),
    ("name", ("dtest030319.",)),
    ("number", (1,)),
    ("places", (4,)),
    ("path", ("/export/images",)),
    ("basename", ("/export/images/dtest030319.0001",)),
    ("ccdTemps", (-113.8,-106.7,)),
    ("ccdHeaters", (0.0,0.0,)),
)
MainDataSet = RO.Alg.OrderedDict(MainDataSet)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
    {}
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":"spicam", "type":":"}
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
