#!/usr/bin/env python
"""Configuration input panel for Kosmos.

History:
2019-12-20 CS       Created
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel
import KosmosModel

_MaxDataWidth = 5

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
    InstName = "Kosmos"
    HelpPrefix = 'Instruments/%s/%sWin.html#' % (InstName, InstName)

    # category names
    CCDCat = "ccd"
    ConfigCat = RO.Wdg.StatusConfigGridder.ConfigCat

    def __init__(self,
        master,
        stateTracker,
    **kargs):
        """Create a new widget to show status for and configure Kosmos

        Inputs:
        - master: parent widget
        - stateTracker: an RO.Wdg.StateTracker
        """
        RO.Wdg.InputContFrame.__init__(self, master=master, stateTracker=stateTracker, **kargs)
        self.model = KosmosModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()

        # set while updating user ccd binning or user window default,
        # to prevent storing new unbinned values for ccd window.
        self._freezeCCDUBWindow = False

        gr = RO.Wdg.StatusConfigGridder(
            master = self,
            sticky = "e",
        )
        self.gridder = gr

        shutterCurrWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "current state of the shutter",
            # helpURL = self.HelpPrefix + "Shutter",
            anchor = "w",
        )
        self.model.shutter.addROWdg(shutterCurrWdg)
        gr.gridWdg ("Shutter", shutterCurrWdg, sticky="ew", colSpan=3)

        self.filter1NameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.filter1NameUserWdg = RO.Wdg.OptionMenu(
            self,
            items = [],
            noneDisplay = "?",
            helpText = "requested filter",
            # helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg (
            label = "Filter1",
            dataWdg = self.filter1NameCurrWdg,
            units = False,
            cfgWdg = self.filter1NameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.filter2NameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.filter2NameUserWdg = RO.Wdg.OptionMenu(
            self,
            items = [],
            noneDisplay = "?",
            helpText = "requested filter",
            # helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg (
            label = "Filter2",
            dataWdg = self.filter2NameCurrWdg,
            units = False,
            cfgWdg = self.filter2NameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.disperserNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.disperserNameUserWdg = RO.Wdg.OptionMenu(
            self,
            items = [],
            noneDisplay = "?",
            helpText = "requested filter",
            # helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg (
            label = "disperser",
            dataWdg = self.disperserNameCurrWdg,
            units = False,
            cfgWdg = self.disperserNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.slitNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.slitNameUserWdg = RO.Wdg.OptionMenu(
            self,
            items = [],
            noneDisplay = "?",
            helpText = "requested filter",
            # helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg (
            label = "slit",
            dataWdg = self.slitNameCurrWdg,
            units = False,
            cfgWdg = self.slitNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.calstageNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.calstageNameUserWdg = RO.Wdg.OptionMenu(
            self,
            items = [],
            noneDisplay = "?",
            helpText = "requested filter",
            # helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg (
            label = "calstage",
            dataWdg = self.calstageNameCurrWdg,
            units = False,
            cfgWdg = self.calstageNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.gfocusNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )

        gr.gridWdg (
            label = "gfocus",
            dataWdg = self.gfocusNameCurrWdg,
            units = False,
            cfgWdg = None,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.camfocNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )

        gr.gridWdg (
            label = "camfoc",
            dataWdg = self.camfocNameCurrWdg,
            units = False,
            cfgWdg = None,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.colfocNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )

        gr.gridWdg (
            label = "colfoc",
            dataWdg = self.colfocNameCurrWdg,
            units = False,
            cfgWdg = None,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )


        self.rowBinNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "current filter or status",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.rowBinNameUserWdg = RO.Wdg.OptionMenu(
            self,
            items = ["1", "2"],
            noneDisplay = "?",
            helpText = "requested row bin factor",
            # helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg (
            label = "rowBin",
            dataWdg = self.rowBinNameCurrWdg,
            units = False,
            cfgWdg = self.rowBinNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.colBinNameCurrWdg = RO.Wdg.StrLabel(
            master = self,
            width = 9, # room for "Not Homed"
            helpText = "column bin factor",
            # helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.colBinNameUserWdg = RO.Wdg.OptionMenu(
            self,
            items = ["1","2"],
            noneDisplay = "?",
            helpText = "requested column bin",
            # helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg (
            label = "colBin",
            dataWdg = self.colBinNameCurrWdg,
            units = False,
            cfgWdg = self.colBinNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )


        # axisLabels = ("row", "col")
        # ccdBinCurrWdgSet = [RO.Wdg.IntLabel(self,
        #     width = 4,
        #     helpText = "current bin factor in %s" % (axis,),
            # helpURL=self.HelpPrefix + "Bin",
        # )
        #     for axis in axisLabels
        # ]
        # self.model.ccdBin.addROWdgSet(ccdBinCurrWdgSet)



        # ccd widgets

        # store user-set window in unbinned pixels
        # so the displayed binned value can be properly
        # updated when the user changes the binning
#         self.userCCDUBWindow = None

#         # ccd image header; the label is a toggle button
#         # for showing ccd image info
#         # grid that first as it is always displayed
#         self.showCCDWdg = RO.Wdg.Checkbutton(
#             master = self,
#             text = "CCD",
#             defValue = False,
#             helpText = "Show binning, etc.?",
            # helpURL = self.HelpPrefix + "ShowCCD",
#         )
#         gr.addShowHideControl(self.CCDCat, self.showCCDWdg)
#         self._stateTracker.trackCheckbutton("showCCD", self.showCCDWdg)
#         gr.gridWdg (
#             label = self.showCCDWdg,
#         )

#         self.fullFrameButton = RO.Wdg.Button(
#             master = self,
#             text = "Set Full Frame",
#             command = self._setFullFrame,
#             helpText = "set ccd window to full frame",
            # helpURL = self.HelpPrefix + "Set Full Frame",
#         )
#         gr.gridWdg(
#             cfgWdg = self.fullFrameButton,
#             cat = self.CCDCat,
#             row = -1,
#             sticky = "e",
#             colSpan = 2,
#         )

#         # grid ccd labels; these show/hide along with all other CCD data
#         axisLabels = ("x", "y")
#         ccdLabelDict = {}
#         for setName in ("data", "cfg"):
#             ccdLabelDict[setName] = [
#                 Tkinter.Label(self,
#                     text=axis,
#                 )
#                 for axis in axisLabels
#             ]
#         gr.gridWdg (
#             label = None,
#             dataWdg = ccdLabelDict["data"],
#             cfgWdg = ccdLabelDict["cfg"],
#             sticky = "e",
#             cat = self.CCDCat,
# #            row = -1,
#         )

#         ccdBinCurrWdgSet = [RO.Wdg.IntLabel(self,
#             width = 4,
#             helpText = "current bin factor in %s" % (axis,),
            # helpURL=self.HelpPrefix + "Bin",
        # )
#             for axis in axisLabels
#         ]
#         self.model.ccdBin.addROWdgSet(ccdBinCurrWdgSet)

#         self.ccdBinUserWdgSet = [
#             RO.Wdg.IntEntry(
#                 master = self,
#                 minValue = 1,
#                 maxValue = 99,
#                 width = 2,
#                 helpText = "requested bin factor in %s" % (axis,),
                # helpURL = self.HelpPrefix + "Bin",
#                 clearMenu = None,
#                 defMenu = "Current",
#                 callFunc = self._userBinChanged,
#                 autoIsCurrent = True,
#             )
#             for axis in axisLabels
#         ]
#         self.model.ccdBin.addROWdgSet(self.ccdBinUserWdgSet, setDefault=True)
#         gr.gridWdg (
#             label = "Bin",
#             dataWdg = ccdBinCurrWdgSet,
#             cfgWdg = self.ccdBinUserWdgSet,
#             cat = self.CCDCat,
#         )

        # CCD window

#         winDescr = (
#             "smallest x",
#             "smallest y",
#             "largest x",
#             "largest y",
#         )
#         ccdWindowCurrWdgSet = [RO.Wdg.IntLabel(self,
#             width = 4,
#             helpText = "%s of current window (binned pix)" % winDescr[ii],
            # helpURL = self.HelpPrefix + "Window",
#         )
#             for ii in range(4)
#         ]
#         self.model.ccdWindow.addROWdgSet(ccdWindowCurrWdgSet)

#         self.ccdWindowUserWdgSet = [
#             RO.Wdg.IntEntry(
#                 master = self,
#                 minValue = 1,
#                 maxValue = (2048, 2048, 2048, 2048)[ii],
#                 width = 4,
#                 helpText = "%s of requested window (binned pix)" % winDescr[ii],
                # helpURL = self.HelpPrefix + "Window",
#                 clearMenu = None,
#                 defMenu = "Current",
#                 minMenu = ("Mininum", "Minimum", None, None)[ii],
#                 maxMenu = (None, None, "Maximum", "Maximum")[ii],
#                 callFunc = self._userWindowChanged,
#                 autoIsCurrent = True,
#                 isCurrent = False,
#             ) for ii in range(4)
#         ]
# #       self.model.ccdUBWindow.addCallback(self._setCCDWindowWdgDef)
#         gr.gridWdg (
#             label = "Window",
#             dataWdg = ccdWindowCurrWdgSet[0:2],
#             cfgWdg = self.ccdWindowUserWdgSet[0:2],
#             units = "LL bpix",
#             cat = self.CCDCat,
#         )
#         gr.gridWdg (
#             label = None,
#             dataWdg = ccdWindowCurrWdgSet[2:4],
#             cfgWdg = self.ccdWindowUserWdgSet[2:4],
#             units = "UR bpix",
#             cat = self.CCDCat,
#         )

#         # Image size, in binned pixels
#         self.ccdImageSizeCurrWdgSet = [RO.Wdg.IntLabel(
#             master = self,
#             width = 4,
#             helpText = "current %s size of image (binned pix)" % winDescr[ii],
            # helpURL = self.HelpPrefix + "Window",
#         )
#             for ii in range(2)
#         ]
# #       self.model.ccdWindow.addCallback(self._updCurrImageSize)

#         self.ccdImageSizeUserWdgSet = [
#             RO.Wdg.IntLabel(
#                 master = self,
#                 width = 4,
#                 helpText = "requested %s size of image (binned pix)" % ("x", "y")[ii],
                # helpURL = self.HelpPrefix + "ImageSize",
#             ) for ii in range(2)
#         ]
#         gr.gridWdg (
#             label = "Image Size",
#             dataWdg = self.ccdImageSizeCurrWdgSet,
#             cfgWdg = self.ccdImageSizeUserWdgSet,
#             units = "bpix",
#             cat = self.CCDCat,
#         )

        # set up format functions for the filter menu
        # this allows us to return index values instead of names
        class indFormat(object):
            def __init__(self, indFunc, offset=1):
                self.indFunc = indFunc
                self.offset = offset
            def __call__(self, inputCont):
                valueList = inputCont.getValueList()
                if not valueList:
                    return ''
                selValue = valueList[0]
                if not selValue:
                    return ''
                name = inputCont.getName()
                return "%s=%d" % (name, self.indFunc(selValue) + self.offset)

        # def myCB(*args, **kwargs):
        #     import pdb; pdb.set_trace()

        # add callbacks that access widgets
        self.model.filter1Names.addCallback(self.filter1NameUserWdg.setItems)
        self.model.filter2Names.addCallback(self.filter2NameUserWdg.setItems)
        self.model.disperserNames.addCallback(self.disperserNameUserWdg.setItems)
        self.model.slitNames.addCallback(self.slitNameUserWdg.setItems)
        self.model.calstageNames.addCallback(self.calstageNameUserWdg.setItems)
        # self.model.calstageNames.addCallback(myCB)


        self.model.filter1.addIndexedCallback(self._updFilter1Name)
        self.model.filter2.addIndexedCallback(self._updFilter2Name)
        self.model.disperser.addIndexedCallback(self._updDisperserName)
        self.model.slit.addIndexedCallback(self._updSlitName)
        self.model.gfocusPos.addIndexedCallback(self._updGfocusName)
        self.model.gfocusState.addIndexedCallback(self._updGfocusState)
        self.model.calstagePos.addIndexedCallback(self._updCalstageName)
        self.model.calstageState.addIndexedCallback(self._updCalstageState)
        self.model.camfoc.addIndexedCallback(self._updCamfocState)
        self.model.colfoc.addIndexedCallback(self._updColfocState)
        self.model.rowBin.addIndexedCallback(self._updRowBinName)
        self.model.colBin.addIndexedCallback(self._updColBinName)


        # self.model.ccdUBWindow.addCallback(self._setCCDWindowWdgDef)
        # self.model.ccdWindow.addCallback(self._updCurrImageSize)

        # set up the input container set; this is what formats the commands
        # and allows saving and recalling commands
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = "filter1",
                    wdgs = self.filter1NameUserWdg,
                    formatFunc = indFormat(self.filter1NameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "filter2",
                    wdgs = self.filter2NameUserWdg,
                    formatFunc = indFormat(self.filter2NameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "disperser",
                    wdgs = self.disperserNameUserWdg,
                    formatFunc = indFormat(self.disperserNameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "slit",
                    wdgs = self.slitNameUserWdg,
                    formatFunc = indFormat(self.slitNameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "calstage",
                    wdgs = self.calstageNameUserWdg,
                    formatFunc = RO.InputCont.BasicFmt(nameSep="="),
                    # formatFunc = indFormat(self.calstageNameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "rowBin",
                    wdgs = self.rowBinNameUserWdg,
                    formatFunc = RO.InputCont.BasicFmt(nameSep="="),
                    # formatFunc = indFormat(self.calstageNameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "colBin",
                    wdgs = self.colBinNameUserWdg,
                    formatFunc = RO.InputCont.BasicFmt(nameSep="="),
                    # formatFunc = indFormat(self.calstageNameUserWdg.index),
                ),
                # RO.InputCont.WdgCont (
                #     name = "amp",
                #     wdgs = self.ampNameUserWdg,
                #     formatFunc = RO.InputCont.BasicFmt(nameSep="="),
                # ),
                # RO.InputCont.WdgCont (
                #     name = "readout",
                #     wdgs = self.readoutRateNameUserWdg,
                #     formatFunc = RO.InputCont.BasicFmt(nameSep="="),
                # ),
                # RO.InputCont.WdgCont (
                #     name = "diffuser",
                #     wdgs = self.diffuserPositionUserWdg,
                #     formatFunc = RO.InputCont.BasicFmt(nameSep="="),
                # ),
                # RO.InputCont.WdgCont (
                #     name = "rotateDiffuser",
                #     wdgs = self.diffuserRotationUserWdg,
                #     formatFunc = RO.InputCont.BasicFmt(nameSep="="),
                # ),
                # RO.InputCont.WdgCont (
                #     name = "bin",
                #     wdgs = self.ccdBinUserWdgSet,
                #     formatFunc = RO.InputCont.BasicFmt(nameSep="=", valSep=","),
                # ),
                # RO.InputCont.WdgCont (
                #     name = "window",
                #     wdgs = self.ccdWindowUserWdgSet,
                #     formatFunc = RO.InputCont.BasicFmt(nameSep="=", valSep=","),
                # ),
            ],
        )

        self.configWdg = RO.Wdg.InputContPresetsWdg(
            master = self,
            sysName = "%sConfig" % (self.InstName,),
            userPresetsDict = self.tuiModel.userPresetsDict,
            stdPresets = dict(),
            inputCont = self.inputCont,
            helpText = "use and manage named presets",
            # helpURL = self.HelpPrefix + "Presets",
        )
        self.gridder.gridWdg(
            "Presets",
            cfgWdg = self.configWdg,
            colSpan = 2,
        )

        self.gridder.allGridded()

        def repaint(evt):
            self.restoreDefault()
        self.bind("<Map>", repaint)

    # def _setFullFrame(self, *args, **kwargs):
    #     currBinList = [wdg.getNum() for wdg in self.ccdBinUserWdgSet]
    #     maxCoordList = self.model.maxCoord(binFac=currBinList)
    #     for i in range(2):
    #         self.ccdWindowUserWdgSet[i].set(1)
    #         self.ccdWindowUserWdgSet[i+2].set(maxCoordList[i])

    # def _saveCCDUBWindow(self):
    #     """Save user ccd window in unbinned pixels.
    #     """
    #     if self._freezeCCDUBWindow:
    #         return

    #     userWindow = [wdg.getNum() for wdg in self.ccdWindowUserWdgSet]
    #     if 0 in userWindow:
    #         return
    #     userBinFac = self._getUserBinFac()
    #     if 0 in userBinFac:
    #         return
    #     self.userCCDUBWindow = self.model.unbin(userWindow, userBinFac)

#     def _setCCDWindowWdgDef(self, *args, **kargs):
#         """Updates the default value of CCD window wdg.
#         If this has the effect of changing the displayed values
#         (only true if a box is blank) then update the saved unbinned window.
#         """
#         if self.userCCDUBWindow is None:
#             currUBWindow, isCurrent = self.model.ccdUBWindow.get()
#             if isCurrent:
#                 self.userCCDUBWindow = currUBWindow

#         initialUserCCDWindow = self._getUserCCDWindow()
#         self._updUserCCDWindow(doCurrValue=False)
#         if initialUserCCDWindow != self._getUserCCDWindow():
# #           print "_setCCDWindowWdgDef; user value changed when default changed; save new unbinned value"
#             self._saveCCDUBWindow()


    # def _userBinChanged(self, *args, **kargs):
    #     """User bin factor changed.
    #     Update ccd window current values and default values.
    #     """
    #     self._updUserCCDWindow()


    # def _userWindowChanged(self, *args, **kargs):
    #     self._saveCCDUBWindow()

    #     # update user ccd image size
    #     actUserCCDWindow = self._getUserCCDWindow()
    #     if 0 in actUserCCDWindow:
    #         return
    #     for ind in range(2):
    #         imSize = 1 + actUserCCDWindow[ind+2] - actUserCCDWindow[ind]
    #         self.ccdImageSizeUserWdgSet[ind].set(imSize)

    # def _updCurrImageSize(self, *args, **kargs):
    #     """Update current image size.
    #     """
    #     window, isCurrent = self.model.ccdWindow.get()
    #     if not isCurrent:
    #         return

    #     try:
    #         imageSize = [1 + window[ind+2] - window[ind] for ind in range(2)]
    #     except TypeError:
    #         imageSize = (None, None)
    #     for ind in range(2):
    #         self.ccdImageSizeCurrWdgSet[ind].set(imageSize[ind])

    # def _updFilterNameOrState(self, *args, **kargs):
    #     """Show current filter name, if stopped at a known position, else state
    #     """
    #     filterState, stateIsCurrent = self.model.filterState.getInd(0)
    #     filterName, filterNameIsCurrent = self.model.currFilter.getInd(1)
    #     cmdFilter, cmdFilterIsCurrent = self.model.cmdFilter.getInd(1)
    #     isOK = True

    #     if filterState is not None and filterState.lower() not in ("moving", "homing"):
    #         if filterName != cmdFilter:
    #             # filter wheel apparently didn't go where it was commanded to go;
    #             # show current and filter widget in pink as a warning
    #             # and set default user to None so any filter can be chosen
    #             filterNameIsCurrent = False
    #             isOK = False
    #         self.filterNameCurrWdg.set(filterName, isCurrent=filterNameIsCurrent)
    #     else:
    #         self.filterNameCurrWdg.set(filterState, isCurrent=stateIsCurrent)
    #     if not isOK:
    #         self.filterNameUserWdg.setDefault(None, doCheck=False)
    #         self.filterNameUserWdg.set(cmdFilter)
    #     elif cmdFilter in (None, "?"):
    #         self.filterNameUserWdg.setDefault(None, doCheck=False)
    #     else:
    #         self.filterNameUserWdg.setDefault(cmdFilter, doCheck=False)

    def _updFilter1Name(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        filter1, isCurrent = self.model.filter1.getInd(0)
        try:
            filterIndex = int(filter1) - 1
            filterName = self.filter1NameUserWdg._items[filterIndex]
            self.filter1NameCurrWdg.set(filterName, severity=RO.Constants.sevNormal)
            self.filter1NameUserWdg.setDefault(filterName, doCheck=False)
        except:
            self.filter1NameCurrWdg.set(filter1, severity=RO.Constants.sevWarning) # probably something like moving

    def _updFilter2Name(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        filter2, isCurrent = self.model.filter2.getInd(0)
        try:
            filterIndex = int(filter2) - 1
            filterName = self.filter2NameUserWdg._items[filterIndex]
            self.filter2NameCurrWdg.set(filterName, severity=RO.Constants.sevNormal)
            self.filter2NameUserWdg.setDefault(filterName, doCheck=False)
        except:
            self.filter2NameCurrWdg.set(filter2, severity=RO.Constants.sevWarning) # probably something like moving

    def _updDisperserName(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        disperser, isCurrent = self.model.disperser.getInd(0)
        try:
            filterIndex = int(disperser) - 1
            filterName = self.disperserNameUserWdg._items[filterIndex]
            self.disperserNameCurrWdg.set(filterName, severity=RO.Constants.sevNormal)
            self.disperserNameUserWdg.setDefault(filterName, doCheck=False)
        except:
            self.disperserNameCurrWdg.set(disperser, severity=RO.Constants.sevWarning) # probably something like moving

    def _updSlitName(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        slit, isCurrent = self.model.slit.getInd(0)
        try:
            filterIndex = int(slit) - 1
            filterName = self.slitNameUserWdg._items[filterIndex]
            self.slitNameCurrWdg.set(filterName, severity=RO.Constants.sevNormal)
            self.slitNameUserWdg.setDefault(filterName, doCheck=False)
        except:
            self.slitNameCurrWdg.set(slit, severity=RO.Constants.sevWarning) # probably something like moving

    def _updCalstageState(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        calstageState, isCurrent = self.model.calstageState.getInd(0)
        if calstageState is None:
            return
        if calstageState == "Moving" or "hom" in calstageState.lower():
            self.calstageNameCurrWdg.set(calstageState, severity=RO.Constants.sevWarning)

    def _updGfocusState(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        gfocusState, isCurrent = self.model.gfocusState.getInd(0)
        if gfocusState is None:
            return
        if gfocusState == "Moving" or "hom" in gfocusState.lower():
            self.gfocusNameCurrWdg.set(gfocusState, severity=RO.Constants.sevWarning)

    def _updCalstageName(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        calstage, isCurrent = self.model.calstagePos.getInd(0)
        self.calstageNameCurrWdg.set(calstage, severity=RO.Constants.sevNormal)
        if calstage is None:
            stagePos = "?"
        elif int(calstage) > 5000:
            stagePos = "in"
        else:
            stagePos = "out"
        self.calstageNameUserWdg.setDefault(stagePos, doCheck=False)

    def _updGfocusName(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        gfocus, isCurrent = self.model.gfocusPos.getInd(0)
        self.gfocusNameCurrWdg.set(gfocus, severity=RO.Constants.sevNormal)

    def _updCamfocState(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        camfoc, isCurrent = self.model.camfoc.getInd(0)
        self.camfocNameCurrWdg.set(camfoc)

    def _updColfocState(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        colfoc, isCurrent = self.model.colfoc.getInd(0)
        self.colfocNameCurrWdg.set(colfoc)

    def _updRowBinName(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        rowBin, isCurrent = self.model.rowBin.getInd(0)
        if rowBin is None:
            rowBin = "?"
        else:
            rowBin = str(int(float(rowBin)))
        self.rowBinNameCurrWdg.set(rowBin, severity=RO.Constants.sevNormal)
        self.rowBinNameUserWdg.setDefault(rowBin, doCheck=False)

    def _updColBinName(self, *args, **kargs):
        """Show current filter name, if stopped at a known position, else state
        """
        colBin, isCurrent = self.model.colBin.getInd(0)
        if colBin is None:
            colBin = "?"
        else:
            colBin = str(int(float(colBin)))
        self.colBinNameCurrWdg.set(colBin, severity=RO.Constants.sevNormal)
        self.colBinNameUserWdg.setDefault(colBin, doCheck=False)

    # def _updUserCCDWindow(self, doCurrValue = True):
    #     """Update user-set ccd window.

    #     Inputs:
    #     - doCurrValue: if True, set current value and default;
    #         otherwise just set default.

    #     The current value is set from the cached user's unbinned value
    #     """
    #     self._freezeCCDUBWindow = True
    #     try:
    #         if doCurrValue and self.userCCDUBWindow is None:
    #             return
    #         userBinFac = self._getUserBinFac()
    #         if 0 in userBinFac:
    #             return

    #         # update user ccd window displayed value, default valud and limits
    #         if doCurrValue:
    #             userWindow = self.model.bin(self.userCCDUBWindow, userBinFac)
    #         currUBWindow, isCurrent = self.model.ccdUBWindow.get()
    #         if isCurrent:
    #             currWindow = self.model.bin(currUBWindow, userBinFac)
    #         else:
    #             currWindow = (None,)*4
    #         minWindowXYXY = self.model.minCoord(userBinFac)*2
    #         maxWindowXYXY = self.model.maxCoord(userBinFac)*2
    #         for ind in range(4):
    #             wdg = self.ccdWindowUserWdgSet[ind]
    #             # disable limits
    #             wdg.setRange(
    #                 minValue = None,
    #                 maxValue = None,
    #             )

    #             # set displayed and default value
    #             if doCurrValue:
    #                 wdg.set(userWindow[ind], isCurrent)
    #             wdg.setDefault(currWindow[ind], isCurrent)

    #             # set correct range for this bin factor
    #             wdg.setRange(
    #                 minValue = minWindowXYXY[ind],
    #                 maxValue = maxWindowXYXY[ind],
    #             )

    #     finally:
    #         self._freezeCCDUBWindow = False

    def _getUserBinFac(self):
        """Return the current user-set bin factor in x and y.
        """
        return [wdg.getNum() for wdg in self.ccdBinUserWdgSet]

    def _getUserCCDWindow(self):
        """Return the current user-set ccd window (binned) in x and y.
        """
        return [wdg.getNum() for wdg in self.ccdWindowUserWdgSet]


if __name__ == "__main__":
    import TestData
    root = TestData.tuiModel.tkRoot
    stateTracker = RO.Wdg.StateTracker(logFunc=TestData.tuiModel.logFunc)

    testFrame = StatusConfigInputWdg(root, stateTracker=stateTracker)
    testFrame.pack()

    TestData.start()

    testFrame.restoreDefault()

    def printCmds():
        print "strList =", testFrame.getStringList()

    bf = Tkinter.Frame(root)
    cfgWdg = RO.Wdg.Checkbutton(bf, text="Config", defValue=True)
    cfgWdg.pack(side="left")
    Tkinter.Button(bf, text="Cmds", command=printCmds).pack(side="left")
    Tkinter.Button(bf, text="Current", command=testFrame.restoreDefault).pack(side="left")
    Tkinter.Button(bf, text="Demo", command=TestData.animate).pack(side="left")
    bf.pack()

    testFrame.gridder.addShowHideControl(testFrame.ConfigCat, cfgWdg)

    root.mainloop()
