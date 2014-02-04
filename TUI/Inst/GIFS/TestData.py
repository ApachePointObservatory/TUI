import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher(actor="gifs", delay=0.5)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    "magnifierConfig=zero, clear, 7x7, 14x14",
    "lensletsConfig=clear, zero, pinhole, wedge, bare_lens",
    "filterPos=1, filter1,  6572.0, 265.0, 0.0",
    "filterPos=2, red_ifs,  6572.0, 265.0, 1.2",
    "filterPos=3, filt6300, 6307.0, 126.0, -23.3",
    "filterPos=4, halpha_a, 6564.0,  10.0, 28.3",
    "filterPos=5, filter5,  6564.0,  10.0, -12.7",
    "filterPos=6, filter6,  6564.0,  10.0, 10.8",
    "collimatorConfig=spect_pinhole_red, spect_pinhole_green, imaging_bare_lens_green, zero, imaging_pinhole_green, imaging_green, spect_bare_lens_red, spect_bare_lens_green, imaging_red, imaging_pinhole_red, imaging_bare_lens_red",
    "disperserConfig=etalon, clear, green, zero, red, hi_res",
    "magnifierStatus=0, zero, 1.0, 1.0",
    "lensletsStatus=0, zero, 0.0, 0.0",
    "calMirrorStatus=in, 0.0",
    "filterStatus=0, 4.0, -120000.0, halpha_a, 6564.0, 10.0, 0.0",
    "collimatorStatus=0, spect_pinhole_red, -3.2, 0.0",
    "disperserStatus=0, zero, 0.0, 0.0",
)

# Each element of animDataSet is list of keywords
AnimDataSet = (
)

def start():
    testDispatcher.dispatch(MainDataList)

def animate():
    testDispatcher.runDataSet(AnimDataSet)
