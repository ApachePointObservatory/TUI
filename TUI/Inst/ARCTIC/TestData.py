#!/usr/bin/env python
"""Data for testing various ARCTIC widgets

History:
2015-10-20 ROwen    Added filterState and switched to currFilter, cmdFilter.
"""
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher(actor="arctic", delay=1)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    'ampNames=LL, Quad',
    'ampName=Quad',
    'filterNames="SDSS u\'", "SDSS g\'", "SDSS r\'", "SDSS i\'", "SDSS z\'"',
    'currFilter=1, "SDSS u\'"',
    'cmdFilter=1, "SDSS u\'"',
    "filterState=Done, 0, 0",
    'shutter="closed"',
    'ccdState="ok"',
    'ccdBin=2,2',
    'ccdWindow=1,1,1024,514',
    'ccdUBWindow=1,1,2048,1028',
    'ccdOverscan=50,0',
    'name="dtest030319."',
    'number=1',
    'places=4',
    'path="/export/images"',
    'basename="/export/images/dtest030319.0001"',
    'ccdTemps=-113.8,-106.7',
    'ccdHeaters=0.0,0.0',
    'readoutRateNames=Slow, Medium, Fast',
    'readoutRateName=Slow',
)
print "MainDataList=", MainDataList

# Each element of animDataSet is list of keywords
AnimDataSet = (
    ('currFilter=NaN, ?', 'cmdFilter=3, "SDSS r\'"', "filterState=Moving, 3, 3", "ampName=UR"),
    ('currFilter=3, "SDSS r\'"', 'cmdFilter=3, "SDSS r\'"', "filterState=Done, 0, 0"),
)

def start():
    testDispatcher.dispatch(MainDataList)

def animate():
    testDispatcher.runDataSet(AnimDataSet)
