#!/usr/bin/env python
from __future__ import division, absolute_import
"""Collect data for the telescope pointing model

To make a quiver plot on a radial plot, simply compute the vectors in x-y
<http://stackoverflow.com/questions/13828800/how-to-make-a-quiver-plot-in-polar-coordinates>
radii = np.linspace(0.5,1,10)
thetas = np.linspace(0,2*np.pi,20)
theta, r = np.meshgrid(thetas, radii)

dr = 1
dt = 1

f = plt.figure()
ax = f.add_subplot(111, polar=True)
ax.quiver(theta, r, dr * cos(theta) - dt * sin (theta), dr * sin(theta) + dt * cos(theta))

History:
2014-04-21 ROwen    Start tinkering
"""
import collections
import glob
import os

import numpy
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import Tkinter

import RO.CanvasUtil
import RO.CnvUtil
import RO.MathUtil
from RO.ScriptRunner import ScriptError
from RO.Comm.Generic import Timer
import RO.Wdg
import TUI.TUIModel
import TUI.TCC.TCCModel
import TUI.TCC.UserModel
import TUI.Inst.ExposeModel
import TUI.Guide.GuideModel

WindowName = "Misc.Get Pointing Data"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "400x400+434+22",
        wdgFunc = ScriptClass,
        defVisible = True,
    )

class InstActors(object):
    def __init__(self, instName, exposeActor, guideActor):
        self.instName = instName
        self.exposeActor = exposeActor
        self.guideActor = guideActor

class ScriptClass(object):
    """Widget to collect pointing data

    @todo:
    - Handle multiple instruments, including binning, and windowing to speed up exposures.
        I propose common code with the focus scripts, and handling multiple instruments identically
        (i.e. either one focus scripts and one pointing data script per instrument,
        or else a single focus script and a single pointing data script, each of which supports all instruments)

        Meanwhile much of this code is borrowed directly from BaseFocusScript,
        even though some of it is not a perfect fit.
    - Add a help page and link to it
    """
    def __init__(self, sr):
        """Construct a ScriptClass

        Inputs:
        - sr: a ScriptRunner
        """
        self.sr = sr
        sr.master.winfo_toplevel().resizable(True, True)
        sr.debug = True
        self.azAltList = []
        self._nextPointTimer = Timer()
        self._gridDirs = getGridDirs()
        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.tccModel.instName.addIndexedCallback(self._setInstName)
        self.guideModel = TUI.Guide.GuideModel.getModel("gcam")
        self.actorData = collections.OrderedDict()
        self.maxFindAmpl = 30000
        self.defRadius = 5.0
        self.helpURL = None
        defBinFactor = 3
        finalBinFactor = None
        if defBinFactor == None:
            self.defBinFactor = None
            self.binFactor = 1
            self.dispBinFactor = 1
        else:
            self.defBinFactor = int(defBinFactor)
            self.binFactor = self.defBinFactor
            self.dispBinFactor = self.defBinFactor
        self.finalBinFactor = finalBinFactor
        self.gcamActor = "gcam"

        self.azAltGraph = AzAltGraph(master=sr.master)
        self.azAltGraph.grid(row=0, column=0)
        sr.master.grid_rowconfigure(0, weight=1)
        sr.master.grid_columnconfigure(0, weight=1)

        ctrlFrame = Tkinter.Frame(sr.master)
        gr = RO.Wdg.Gridder(ctrlFrame)
        self._gridDict = dict()
        self.gridWdg = RO.Wdg.OptionMenu(
            master = ctrlFrame,
            label = "Az/Alt Grid",
            callFunc = self._setGrid,
            items = (),
            postCommand = self._fillGridsMenu,
            helpText = "az/alt grid",
        )
        gr.gridWdg(self.gridWdg.label, self.gridWdg)
        self.instWdg = RO.Wdg.OptionMenu(
            master = ctrlFrame,
            items = (),
            helpText = "instrument or guider to use to measure pointing error",
        )
#        gr.gridWdg("Instrument", self.instWdg)
        gr.startNewCol()
        self.numExpWdg = RO.Wdg.IntEntry(
            master = ctrlFrame,
            label = "Num Exp",
            defValue = 1,
            minValue = 1,
            helpText = "number of exposures (and corrections) per star",
        )
        gr.gridWdg(self.numExpWdg.label, self.numExpWdg)
        self.expTimeWdg = RO.Wdg.FloatEntry(
            master = ctrlFrame,
            label = "Exp Time",
            defValue = 5.0,
            minValue = 0,
            helpText = "exposure time",
        )
        gr.gridWdg(self.expTimeWdg.label, self.expTimeWdg, "sec")
        ctrlFrame.grid(row=1, column=0, sticky="w")

        self.binFactorWdg = RO.Wdg.IntEntry(
            master = ctrlFrame,
            label = "Bin Factor",
            minValue = 1,
            maxValue = 1024,
            defValue = self.defBinFactor or 1,
            defMenu = "Default",
            callFunc = self.updBinFactor,
            helpText = "Bin factor (for rows and columns)",
            helpURL = self.helpURL,
        )
        if self.defBinFactor != None:
            gr.gridWdg(self.binFactorWdg.label, self.binFactorWdg)

        self.centroidRadWdg = RO.Wdg.IntEntry(
            master = ctrlFrame,
            label = "Centroid Radius",
            minValue = 5,
            maxValue = 1024,
            defValue = self.defRadius,
            defMenu = "Default",
            helpText = "Centroid radius; don't skimp",
            helpURL = self.helpURL,
        )
        gr.gridWdg(self.centroidRadWdg.label, self.centroidRadWdg, "arcsec")

        if sr.debug:
            self.tccModel.instName.set(["DIS"],)

    def _setInstName(self, instName, *args, **kwargs):
        """Call when the TCC reports a new instName
        """
        if instName is None:
            return
        return

        # some variant of the following will probably be wanted, once I unify the code with focus scripts
        #...
        if self.sr.isExecuting():
            self.sr.showMsg(
                "Instrument changed from %r to %r while running" % (self.exposeModel.instName, instName),
                severity = RO.Constants.sevError,
            )
            self.cancel()

        try:
            self.exposeModel = TUI.Inst.ExposeModel.getModel(instName)
        except Exception:
            self.exposeModel = None
            self.sr.showMsg(
                "No model for instrument %r" % (instName,),
                severity = RO.Constants.sevWarning,
            )
            self.actorData = collections.OrderedDict()
        else:
            instInfo = self.exposeModel.instInfo
            centroidActor = instInfo.centroidActor
            guiderActor = instInfo.guiderActor
            actorData = collections.OrderedDict()
            if guiderActor:
                guiderName = TUI.Inst.ExposeModel.GuiderActorNameDict.get(guiderActor, guiderActor)
                actorData[guiderName] = InstActors(
                    name = guiderName,
                    exposeActor = None,
                    guiderActor = guiderActor,
                )
            if centroidActor:
                actorData[self.exposeModel.instName] = InstActors(
                    name = self.exposeModel.instName,
                    exposeActor = self.exposeModel.instInfo.exposeActor,
                    guiderActor = self.exposeModel.instInfo.centroidActor,
                 )
            instNames = actorData.keys()
            self.instWdg.setItems(instNames)
            if instNames:
                self.instWdg.setDefault(instNames[0], showDefault=True)
            else:
                self.instWdg.setDefault(None, showDefault=True)

    def _fillGridsMenu(self):
        """Set items of the Grids menu based on available grid files and update self._gridDict
        """
        oldGridNames = set(self._gridDict)
        self._gridDict = self._findGrids()
        gridNames = set(self._gridDict)
        if gridNames != oldGridNames:
            self.gridWdg.setItems(sorted(gridNames))

    def _findGrids(self):
        """Search for available grid files and return as a dict of grid name: file path

        Grid files are *.dat files in TUI/Grids and TUIAdditions/Grids
        """
        gridDict = dict()
        for dirPath in self._gridDirs:
            gridPathList = glob.glob(os.path.join(dirPath, "*.dat"))
            for gridPath in gridPathList:
                gridName = os.path.splitext(os.path.basename(gridPath))[0]
                gridDict[gridName] = gridPath
        return gridDict

    def _setGrid(self, wdg=None):
        """Set a particular grid based on the selected name in self.gridWdg
        """
        gridName = self.gridWdg.getString()
        if not gridName:
            return
        gridPath = self._gridDict[gridName]
        with open(gridPath, "rU") as gridFile:
            azAltList = []
            for i, line in enumerate(gridFile):
                line = line.strip()
                if not line or line[0] in ("#", "!"):
                    continue
                try:
                    az, alt = [float(val) for val in line.split()]
                    azAltList.append((az, alt))
                except Exception:
                    self.sr.showMsg("Cannot parse line %s as az alt: %r\n" % (i+1, line),
                        severity = RO.Constants.sevWarning, isTemp=True)
        self.azAltList = azAltList
        self.azAltGraph.plotAzAltPoints(azAltList)

    def enableCmdBtns(self, doEnable):
        """Enable or disable command buttons (e.g. Expose and Sweep).
        """
        self.gridWdg.setEnable(doEnable)
        self.instWdg.setEnable(doEnable)

    def run(self, sr):
        """Take a set of pointing data
        """
        self.initAll()

        if not self.azAltList:
            raise ScriptError("No az/alt grid selected")
        
        self.recordUserParams(doStarPos=False)

        # set self.relStarPos to center of pointing error probe
        # (the name is a holdover from BaseFocusScript; the field is the location to centroid stars)
        yield sr.waitCmd("tcc", "show inst/full") # make sure we have current guide probe info
        if sr.debug:
            self.relStarPos = [512, 512]
            self.ptErrProbe = 1
        else:
            ptErrProbe = self.tccModel.ptErrProbe.getInd(0)[0]
            if ptErrProbe in (0, None):
                raise ScriptError("Invalid pointing error probe %s; must be >= 1" % (ptErrProbe,))
            guideProbe = self.tccModel.guideProbeDict.get(ptErrProbe)
            if guideProbe is None:
                raise ScriptError("No data for pointing error probe %s" % (ptErrProbe,))
            if not guideProbe.exists:
                raise ScriptError("Pointing error probe %s is disabled" % (ptErrProbe,))
            self.ptErrProbe = ptErrProbe
            self.relStarPos = guideProbe.ctrXY[:]

        for az, alt in self.azAltList[:]:
            # use a copy in case somebody alters the list while running, though that should not be possible
            yield sr.waitCmd(
                actor = "tcc",
                cmdStr = "track %0.7f, %0.7f obs/pterr=(find, refSlew)" % (az, alt),
                keyVars = (self.tccModel.ptRefStar,),
            )
            cmdVar = sr.value
            ptRefStarValues = cmdVar.getLastKeyVarData(self.tccModel.ptRefStar, ind=None)
            if not ptRefStarValues:
                if not sr.debug:
                    raise ScriptError("No pointing reference star found")
                else:
                    ptRefStarValues = (20, 80, 0, 0, 0, 0, "ICRS", 2000, 7)
            self.ptRefStar = PtRefStar(ptRefStarValues)
            numExp = self.numExpWdg.getNum()
            for expInd in range(numExp):
                if expInd == 0:
                    yield self.waitFindStar(firstOnly=True)
                else:
                    yield self.waitCentroid()
                starMeas = sr.value
                if starMeas.xyPos is None:
                    break

                yield self.waitComputePtErr(starMeas)
                ptErr = sr.value

                # log absolute error (ignoring current calib and guide offsets)

                # correct relative error (using current calib and guide offsets)
                yield sr.waitCmd(
                    actor = "tcc",
                    cmdStr = "offset calib %s, %s" % (ptErr.ptErr[0], ptErr.ptErr[1])
                )

    def waitComputePtErr(self, starMeas):
        yield self.sr.waitCmd(
            actor = "tcc",
            cmdStr = "PtCorr %0.6f, %0.6f, %s=%s GuideProbe=%s" % (
                self.ptRefStar.pos[0], self.ptRefStar.pos[1],
                self.ptRefStar.coordSysName,
                self.ptRefStar.coordSysDate,
                self.ptErrProbe
            ),
            keyVars = (self.tccModel.ptCorr, self.tccModel.ptData),
        )
        cmdVar = self.sr.value
        ptCorrValueList = cmdVar.getLastKeyVarData(self.tccModel.ptCorr, ind=None)
        if not ptCorrValueList:
            if self.sr.debug:
                # pt err az, alt, pt pos az, alt
                ptCorrValueList = (0.001, -0.002, 0.011, 0.012)
            else:
                raise ScriptError("ptCorr keyword not seen")
        ptDataValueList = cmdVar.getLastKeyVarData(self.tccModel.ptData, ind=None)
        if not ptDataValueList:
            if self.sr.debug:
                # des phys az, alt, real mount az, alt
                ptDataValueList = (20, 80, 20.001, 79.002)
            else:
                raise ScriptError("ptData keyword not seen")

        self.sr.value = PtErr(
            ptErr = ptCorrValueList[0:2],
            desPhysPos = ptDataValueList[0:2],
            mountPos = ptDataValueList[2:4],
        )

    def formatBinFactorArg(self, isFinal):
        """Return bin factor argument for expose/centroid/findstars command
        
        Inputs:
        - isFinal: if True then return parameters for final exposure
        """
        #print "defBinFactor=%r, binFactor=%r" % (self.defBinFactor, self.binFactor)
        binFactor = self.getBinFactor(isFinal=isFinal)
        if binFactor == None:
            return ""
        return "bin=%d" % (binFactor,)
    
    def formatExposeArgs(self, doWindow=True, isFinal=False):
        """Format arguments for exposure command.
        
        Inputs:
        - doWindow: if true, window the exposure (if permitted)
        - isFinal: if True then return parameters for final exposure
        """
        argList = [
            "time=%s" % (self.expTime,),
            self.formatBinFactorArg(isFinal=isFinal),
            self.formatWindowArg(doWindow),
        ]
        argList = [arg for arg in argList if arg]
        return " ".join(argList)
    
    def formatWindowArg(self, doWindow=True):
        """Format window argument for expose/centroid/findstars command.
        
        Inputs:
        - doWindow: if true, window the exposure (if permitted)
        """
        if not doWindow or not self.doWindow:
            return ""
        if self.windowIsInclusive:
            urOffset = self.windowOrigin
        else:
            urOffset = self.windowOrigin + 1
        windowLL = [self.window[ii] + self.windowOrigin for ii in range(2)]
        windowUR = [self.window[ii+2] + urOffset for ii in range(2)]
        return "window=%d,%d,%d,%d" % (windowLL[0], windowLL[1], windowUR[0], windowUR[1])

    def getEntryNum(self, wdg):
        """Return the numeric value of a widget, or raise ScriptError if blank.
        """
        numVal = wdg.getNumOrNone()
        if numVal != None:
            return numVal
        raise self.sr.ScriptError(wdg.label + " not specified")
    
    def getBinFactor(self, isFinal):
        """Get bin factor (as a single int), or None if not relevant
        
        Inputs:
        - isFinal: if True then return parameters for final exposure
        """
        if self.defBinFactor == None:
            return None

        if isFinal and self.finalBinFactor != None:
            return self.finalBinFactor
        return self.binFactor

    def getExposeCmdDict(self, doWindow=True, isFinal=False):
        """Get basic command arument dict for an expose command
        
        This includes actor, cmdStr, abortCmdStr

        Inputs:
        - doWindow: if true, window the exposure (if permitted)
        - isFinal: if True then return parameters for final exposure
        """
        return dict(
            actor = self.gcamActor,
            cmdStr = "expose " + self.formatExposeArgs(doWindow, isFinal=isFinal),
            abortCmdStr = "abort",
        )

    def initAll(self):
        """Initialize variables, table and graph.
        """
        # initialize shared variables
        self.doTakeFinalImage = False
        self.focDir = None
        self.currBoreXYDeg = None
        self.begBoreXYDeg = None
        self.instScale = None
        self.arcsecPerPixel = None
        self.instCtr = None
        self.instLim = None
        self.cmdMode = None
        self.expTime = None
        self.absStarPos = None
        self.relStarPos = None
        self.binFactor = None
        self.window = None # LL pixel is 0, UL pixel is included

        # data from tcc tinst:I_NA2_DIS.DAT 18-OCT-2006
        # this is a hack; get from tccModel once we support multiple instruments
        self.instScale = [-12066.6, 12090.5] # unbinned pixels/deg
        self.instCtr = [240, 224]
        self.instLim = [0, 0, 524, 511]
        self.arcsecPerPixel = 3600.0 * 2 / (abs(self.instScale[0]) + abs(self.instScale[1]))

        self.enableCmdBtns(False)
    
    def recordUserParams(self, doStarPos=True):
        """Record user-set parameters relating to exposures but not to focus
        
        Inputs:
        - doStarPos: if true: save star position and related information;
            warning: if doStarPos true then there must *be* a valid star position
        
        Set the following instance variables:
        - expTime
        - centroidRadPix
        The following are set to None if doStarPos false:
        - absStarPos
        - relStarPos
        - window
        """
        self.expTime = self.getEntryNum(self.expTimeWdg)
        self.binFactor = self.dispBinFactor
        centroidRadArcSec = self.getEntryNum(self.centroidRadWdg)
        self.centroidRadPix = centroidRadArcSec / (self.arcsecPerPixel * self.binFactor)
        
        if doStarPos:
            winRad = self.centroidRadPix * self.WinSizeMult
            
            self.absStarPos = [None, None]
            for ii in range(2):
                wdg = self.starPosWdgSet[ii]
                self.absStarPos[ii] = self.getEntryNum(wdg)
            
            if self.doWindow:
                windowMinXY = [max(self.instLim[ii],   int(0.5 + self.absStarPos[ii] - winRad)) for ii in range(2)]
                windowMaxXY = [min(self.instLim[ii-2], int(0.5 + self.absStarPos[ii] + winRad)) for ii in range(2)]
                self.window = windowMinXY + windowMaxXY
                self.relStarPos = [self.absStarPos[ii] - windowMinXY[ii] for ii in range(2)]
                #print "winRad=%s, windowMinXY=%s, relStarPos=%s" % (winRad, windowMinXY, self.relStarPos)
            else:
                self.window = None
                self.relStarPos = self.absStarPos[:]
        else:
            self.absStarPos = None
            self.relStarPos = None
            self.window = None

    def updBinFactor(self, *args, **kargs):
        """Called when the user changes the bin factor"""
        newBinFactor = self.binFactorWdg.getNum()
        if newBinFactor <= 0:
            return
        oldBinFactor = self.dispBinFactor
        if oldBinFactor == newBinFactor:
            return

        self.dispBinFactor = newBinFactor

    def waitCentroid(self):
        """Take an exposure and centroid using 1x1 binning.
        
        If the centroid is found, sets self.sr.value to the FWHM.
        Otherwise sets self.sr.value to None.
        """
        centroidCmdStr = "centroid on=%0.1f,%0.1f cradius=%0.1f %s" % \
            (self.relStarPos[0], self.relStarPos[1], self.centroidRadPix, self.formatExposeArgs())
        self.doTakeFinalImage = True
        yield self.sr.waitCmd(
           actor = self.gcamActor,
           cmdStr = centroidCmdStr,
           keyVars = (self.guideModel.files, self.guideModel.star),
           checkFail = False,
        )
        cmdVar = self.sr.value
        if self.sr.debug:
            starData = makeStarData("c", self.relStarPos)
        else:
            starData = cmdVar.getKeyVarData(self.guideModel.star)
        if starData:
            self.sr.value = StarMeas.fromStarKey(starData[0])
            return
        else:
            self.sr.value = StarMeas()

        if not cmdVar.getKeyVarData(self.guideModel.files):
            raise self.sr.ScriptError("exposure failed")

    def waitExtraSetup(self):
        """Executed once at the start of each run
        after calling initAll and getInstInfo but before doing anything else.
        
        Override to do things such as move the boresight or put the instrument into a particular mode.
        """
        yield self.sr.waitMS(1)

    def waitFindStar(self, firstOnly=False):
        """Take a full-frame exposure and find the best star that can be centroided.

        Sets self.sr.value to StarMeas.
        Displays a warning if no star found.
        """
        if self.maxFindAmpl == None:
            raise RuntimeError("Find disabled; maxFindAmpl=None")

        self.sr.showMsg("Exposing %s sec to find best star" % (self.expTime,))
        findStarCmdStr = "findstars " + self.formatExposeArgs(doWindow=False)
        
        self.doTakeFinalImage = True
        yield self.sr.waitCmd(
           actor = self.gcamActor,
           cmdStr = findStarCmdStr,
           keyVars = (self.guideModel.files, self.guideModel.star),
           checkFail = False,
        )
        cmdVar = self.sr.value
        if self.sr.debug:
            filePath = "debugFindFile"
        else:
            if not cmdVar.getKeyVarData(self.guideModel.files):
                raise self.sr.ScriptError("exposure failed")
            fileInfo = cmdVar.getKeyVarData(self.guideModel.files)[0]
            filePath = "".join(fileInfo[2:4])

        if self.sr.debug:               
            starDataList = makeStarData("f", (50.0, 75.0))
        else:
            starDataList = cmdVar.getKeyVarData(self.guideModel.star)
        if not starDataList:
            self.sr.value = StarMeas()
            self.sr.showMsg("No stars found", severity=RO.Constants.sevWarning)
            return
        
        if firstOnly:
            starDataList = starDataList[0:1]
        yield self.waitFindStarInList(filePath, starDataList)

    def waitFindStarInList(self, filePath, starDataList):
        """Find best centroidable star in starDataList.

        If a suitable star is found: set starXYPos to position
        and self.sr.value to the star FWHM.
        Otherwise log a warning and set self.sr.value to None.
        
        Inputs:
        - filePath: image file path on hub, relative to image root
            (e.g. concatenate items 2:4 of the guider Files keyword)
        - starDataList: list of star keyword data
        """
        if self.maxFindAmpl == None:
            raise RuntimeError("Find disabled; maxFindAmpl=None")
        
        for starData in starDataList:
            starXYPos = starData[2:4]
            starAmpl = starData[14]
            if (starAmpl == None) or (starAmpl > self.maxFindAmpl):
                continue
                
            self.sr.showMsg("Centroiding star at %0.1f, %0.1f" % tuple(starXYPos))
            centroidCmdStr = "centroid file=%s on=%0.1f,%0.1f cradius=%0.1f" % \
                (filePath, starXYPos[0], starXYPos[1], self.centroidRadPix)
            yield self.sr.waitCmd(
               actor = self.gcamActor,
               cmdStr = centroidCmdStr,
               keyVars = (self.guideModel.star,),
               checkFail = False,
            )
            cmdVar = self.sr.value
            if self.sr.debug:
                starData = makeStarData("f", starXYPos)
            else:
                starData = cmdVar.getKeyVarData(self.guideModel.star)
            if starData:
                self.sr.value = StarMeas.fromStarKey(starData[0])
                return

        self.sr.showMsg("No usable star fainter than %s ADUs found" % self.maxFindAmpl,
            severity=RO.Constants.sevWarning)
        self.sr.value = StarMeas()

    def end(self, sr):
        self.gridWdg.setEnable(True)
        self.instWdg.setEnable(True)


class AzAltGraph(Tkinter.Frame):
    """Display points in an Az/Alt grid

    az 0 deg is down, 90 deg is right
    alt 90 deg is in the center
    """
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)
        plotFig = matplotlib.figure.Figure(figsize=(6, 6), frameon=False)
        self.figCanvas = FigureCanvasTkAgg(plotFig, self)
        self.figCanvas.get_tk_widget().grid(row=0, column=0, sticky="news")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.axis = plotFig.add_subplot(1, 1, 1, polar=True, autoscale_on=False)
        self._setLimits()

    def _setLimits(self):
        """Update plot limits; must be done for every call to plotAzAltPoints
        """
        self.axis.set_xticklabels(['90', '135', '180', '-135', '-90', '-45', '0', '45'])
        self.axis.set_ylim(0, 90)
        self.axis.set_yticklabels([]) # ['80', '', '60', '', '40', '', '20', '', '0'])

    def plotAzAltPoints(self, azAltPoints):
        """Plot az/alt points
        """
        self.axis.clear()

        # convert az, alt to r, theta, where r is 0 in the middle and theta is 0 right, 90 up
        az, alt = zip(*azAltPoints)
        r = numpy.subtract(90, alt)
        theta = numpy.deg2rad(numpy.subtract(az, 90))
        self.axis.plot(theta, r, linestyle="none", marker="o", markersize=2)
        self._setLimits()
        self.figCanvas.draw()

    def plotErrors(self, azAltPoints, errPoints=()):
        """Plot error data

        Inputs:
        - azAltPoints: az,alt points at which errors were measured
        - errPoints: az,alt error at each az, alt point
        """
        if len(errPoints) != len(azAltPoints):
            raise RuntimeError("len(azAltPoints) = %s != %s = len(errPoints)" % (len(azAltPoints), len(errPoints)))

        # convert az, alt to r, theta, where r is 0 in the middle and theta is 0 right, 90 up
        az, alt = zip(*azAltPoints)
        r = numpy.subtract(90, alt)
        theta = numpy.deg2rad(numpy.subtract(az, 90))

        # quiver on a polar plot takes these strange arguments: theta, r, dx, dy
        sinAz = numpy.sin(numpy.deg2rad(az))
        cosAz = numpy.cos(numpy.deg2rad(az))
        azErr, altErr = zip(*errPoints)
        xErr = (cosAz * azErr) - (sinAz * altErr)
        yErr = (sinAz * azErr) + (cosAz * altErr)
        self.axis.quiver(theta, r, xErr, yErr, width=0.005)
        self.figCanvas.draw()


def getGridDirs():
    """Return grid directories

    Return order is:
    - built-in
    - local TUIAdditions/Scripts
    - shared TUIAdditions/Scripts
    """
    # look for TUIAddition script dirs
    addPathList = TUI.TUIPaths.getAddPaths()
    addScriptDirs = [os.path.join(path, "Grids") for path in addPathList]
    addScriptDirs = [path for path in addScriptDirs if os.path.isdir(path)]

    # prepend the standard script dir and remove duplicates
    stdScriptDir = TUI.TUIPaths.getResourceDir("Grids")
    scriptDirs = [stdScriptDir] + addScriptDirs
    scriptDirs = RO.OS.removeDupPaths(scriptDirs)
    return scriptDirs


class StarMeas(object):
    def __init__(self,
        xyPos = None,
        sky = None,
        ampl = None,
        fwhm = None,
    ):
        self.xyPos = xyPos
        self.sky = sky
        self.ampl = ampl
        self.fwhm = fwhm
    
    @classmethod
    def fromStarKey(cls, starKeyData):
        """Create an instance from star keyword data.
        """
        return cls(
            fwhm = starKeyData[8],
            sky = starKeyData[13],
            ampl = starKeyData[14],
            xyPos = starKeyData[2:4],
        )

class PtErr(object):
    """Pointing error data
    """
    def __init__(self, ptErr, desPhysPos, mountPos):
        """Construct a PtErr object

        Inputs:
        - ptErr: az, alt pointing error relative to current calibration and guide offsets (deg)
        - desPhysPos: desired physical position
        - mountPos: current mount position
        """
        self.ptErr = ptErr
        self.desPhysPos = desPhysPos
        self.mountPos = mountPos

class PtRefStar(object):
    """Information about a pointing reference star
    """
    def __init__(self, valueList):
        """Construct a PtRefStar from a ptRefStar keyword value list
        """
        if valueList[0] == None:
            raise RuntimeError("Invalid data")
        self.pos = valueList[0:2]
        self.parallax = valueList[2]
        self.pm = valueList[3:5]
        self.radVel = valueList[5]
        self.coordSysName = valueList[6]
        self.coordSysDate = valueList[7]
        self.mag = valueList[8]


def makeStarData(
    typeChar = "f",
    xyPos = (10.0, 10.0),
    sky = 200,
    ampl = 1500,
    fwhm = 2.5,
):
    """Make a list containing one star data list for debug mode"""
    xyPos = [float(xyPos[ii]) for ii in range(2)]
    fwhm = float(fwhm)
    return [[typeChar, 1, xyPos[0], xyPos[1], 1.0, 1.0, fwhm * 5, 1, fwhm, fwhm, 0, 0, ampl, sky, ampl]]
