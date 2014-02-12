import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher(actor="gifs", delay=0.5)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    "ccdTemp=250.1; heaterPower=12.3",

    "collimatorConfig=spect_pinhole_red, spect_pinhole_green, imaging_bare_lens_green, zero, imaging_pinhole_green, imaging_green, spect_bare_lens_red, spect_bare_lens_green, imaging_red, imaging_pinhole_red, imaging_bare_lens_red",
    "disperserConfig=etalon, clear, green, zero, red, hi_res",
    "filterNames=filter1, red_ifs, filt6300, halpha_a, filter5, filter6",
    "lensletsConfig=clear, zero, pinhole, wedge, bare_lens",
    "magnifierConfig=zero, clear, 7x7, 14x14",

    "calMirrorStatus=0, in, 0.0, 0.0",
    "collimatorStatus=0, spect_pinhole_red, spect_pinhole_red, -3.2, 0.0, 0.0",
    "disperserStatus=0, green, green, 1200.0, 0.0, 0.0",
    "filterStatus=0, 4.0, -120000.0, halpha_a, 6564.0, 10.0, 0.0, 0.0",
    "lensletsStatus=0, pinhole, pinhole, -523.0, 0.0, 0.0",
    "magnifierStatus=0, 7x7, 7x7, 321.0, 0.0, 0.0",

    "presetNames=foo, bar, baz",
    "presetCalMirrors=in, out, in",
    "presetCollimators=imaging_green, imaging_bare_lens_green, spect_bare_lens_red",
    "presetDispersers=etalon, green, clear",
    "presetFilters=red_ifs, filt6300, halpha_a",
    "presetLenslets=clear, wedge, pinhole",
    "presetMagnifiers=7x7, clear, 14x14",
)

# Each element of animDataSet is list of keywords
AnimDataSet = (
    ("collimatorStatus=1, spect_pinhole_red, imaging_green, -3.2, 32450.0, 1.5",),
    ("filterStatus=1, 2.0, -120000.0, red_ifs, 6564.0, 10.0, 0.0, 2.0"),
    ("calMirrorStatus=1, in, 0.0, 1.0"),
    ("collimatorStatus=0, imaging_green, imaging_green, 32450.0, 0.0, 0",),
    ("calMirrorStatus=0, out, 0.0, 0.0"),
    ("filterStatus=0, 2.0, -120000.0, red_ifs, 6564.0, 10.0, 0.0, 0.0"),
)

def start():
    testDispatcher.dispatch(MainDataList)

def animate():
    testDispatcher.runDataSet(AnimDataSet)
