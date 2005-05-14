#!/usr/local/bin/python
"""Guiding support

To do:
- Arrange buttons in two rows
  or only show buttons that are appropriate?
  (i.e. no need to show start guide and stop guide at the same time
  but also don't want to simply rename buttons--too easy to double-click)
- Enable/disable buttons appropriately
- Test and clean up manual guiding. I really think the loop is going to
  have to be in the hub, but if not:
  - how do I notify users I'm manually guiding?
  - how do I sensibly  handle halting manual vs auto guiding?
    I don't want 2 buttons for this, but I also want to do the right thing reliably.
	Maybe change "Guide Stop" to "Man Guide Stop"?

- clean up ctrl-click messages; they should go away on a successful ctrl-click
  (probably a message saying "centering on ..." should be printed)
  
- Check: if a users presses Expose while guiding what happens?
  We want the user to see their image and not be overwhelmed with
  other images, so I think it should be shown even if "Current"
  is unchecked. Question: do we uncheck "Current" when Expose is pressed?
  I think NOT unless users demand it; it's more transparent that way.

- Add filter wheel controls for ecam (in a separate module--likely a subclass)
- Add filter wheel and focus controls for gcam (in a separate module)
- Add boresight display
- Add predicted star position display and/or...
- Add some kind of display of what guide correction was made;
  preferably a graph that shows a history of guide corrections
  perhaps as a series of linked(?) lines, with older ones dimmer until fade out?
- Add slit display
- Add snap points for dragging along slit -- a big job
- Add ability to see masked data and mask
- Work with Craig to handle "expired" images better.
  These are images that can no longer be used for guiding
  because the telescope has moved.
- Use color prefs for markers
- Add preference to limit # of images saved to disk.
  Include an option to keep images on quit or ask, or always just delete?


History:
2005-02-10 ROwen	alpha version; lots of work to do
2005-02-22 ROwen	Added drag to centroid. Modified for GryImageDispWdg 2005-02-22.
2005-02-23 ROwen	Added exposure time; first cut at setting exp time and thresh when a new image comes in.
2005-03-28 ROwen	Modified for improved files and star keywords.
2005-03-31 ROwen	Implemented hub commands. Added display of current image name.
2005-04-11 ROwen	Modified for GCamModel->GuideModel
2005-04-12 ROwen	Added display of data about selected star.
					Improved to run in normal mode by default and local mode during tests.
2005-04-13 ROwen	Added Stop Guiding and Guide On Boresight.
					Bug fix: mis-handled star data when multiple images used the same (cmdr,cmdID).
2005-04-15 ROwen	Modified to set exposure time and bin factor from the fits image header.
					Modified to send exposure time and bin factor in commands that expose.
					Bug fix: displayed new annotations on the wrong image while the new image was downloading.
2005-04-18 ROwen	Modified to only download guide images if this widget is visible.
					Modified to delete images from disk when they fall off the history list
					or when the application exits (but not in local test mode).
					Initial default exposure time and bin factor are now set from the model.
					Modified to use updated test code.
2005-04-21 ROwen	Added control-click to center on a point and removed the center Button.
					Most errors now write to the status bar (imageRoot unknown is still an exception).
2005-04-26 ROwen	Added preliminary history navigation; it needs some cleanup.
					Added attribute "deviceSpecificFrame" for device-specific controls.
2005-04-27 ROwen	Finished logic for history controls.
					Finished error handling in BasicImObj.
2005-05-13 ROwen	Added preliminary support for manual guiding.
					Re-added the Center button.
					Added references to html help.
					Mod. to pack the widgets instead of gridding them.
					Added _DebugFileDel flag and commented out the remaining
					non-flag-protected diagnostic print statement.
"""
import atexit
import os
import weakref
import Tkinter
import numarray as num
import pyfits
import RO.Alg
import RO.CanvasUtil
import RO.Constants
import RO.Comm.FTPGet as FTPGet
import RO.DS9
import RO.KeyVariable
import RO.ScriptRunner
import RO.Wdg
import RO.Wdg.GrayImageDispWdg as GImDisp
import TUI.TUIModel
import GuideModel
import GuideTest

_HelpPrefix = "Guiding/index.html#"

_MaxDist = 15
_CentroidTag = "centroid"
_FindTag = "findStar"
_GuideTag = "guide"
_SelTag = "showSelection"
_DragRectTag = "centroidDrag"
_MarkRad = 15
_HoleRad = 3

_HistLen = 100

# set these via color prefs, eventually
_FindColor = "green"
_CentroidColor = "cyan"
_GuideColor = "red"

_TypeTagColorDict = {
	"c": (_CentroidTag, _CentroidColor),
	"f": (_FindTag, _FindColor),
#	"g": (_GuideTag, _GuideColor),
}

_LocalMode = False # leave false here; change in test code that imports this module if required
_DebugFileDel = True # print a message when a file is deleted from disk?

_ImSt_Ready = "ready to download"
_ImSt_Downloading = "downloading"
_ImSt_Downloaded = "downloaded"
_ImSt_FileReadFailed = "cannot read file"
_ImSt_DownloadFailed = "download failed"

class BasicImObj:
	def __init__(self,
		baseDir,
		imageName,
		guideModel,
		fetchCallFunc = None
	):
		self.baseDir = baseDir
		self.imageName = imageName
		self.maskObj = None
		self.guideModel = guideModel
		self.state = _ImSt_Ready
		self.exception = None
		self.fetchCallFunc = fetchCallFunc

	def fetchFile(self):
		"""Start downloading the file."""
		if not _LocalMode:
			# pre-pend directory information
			(host, rootDir), isCurr = self.guideModel.imageRoot.get()
			if None in (host, rootDir):
				self.state = _ImSt_DownloadFailed
				self.exception = "server info (imageRoot) not yet known"
				if self.fetchCallFunc:
					self.fetchCallFunc
				return

			# do NOT use os.path to join remote host path components;
			# simply concatenate instead
			fromPath = rootDir + self.imageName

			toPath = self.getLocalPath()
			
			self.guideModel.ftpLogWdg.getFile(
				host = host,
				fromPath = fromPath,
				toPath = toPath,
				isBinary = True,
				overwrite = False,
				createDir = True,
				callFunc = self._fetchCallFunc,
				dispStr = self.imageName,
				username = "images",
				password = "7nights."
			)

		else:
			self.state = _ImSt_Downloaded
			if self.fetchCallFunc:
				self.fetchCallFunc(self)
	
	def getFITSObj(self):
		"""If the file is available, return a pyfits object,
		else return None.
		"""
		if self.state == _ImSt_Downloaded:
			try:
				return pyfits.open(self.getLocalPath())
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				self.state = _ImSt_FileReadFailed
				self.exception = e
		return None
	
	def getLocalPath(self):
		"""Return the full local path to the image."""
		return os.path.join(self.baseDir, self.imageName)
	
	def getStateStr(self):
		"""Return a string describing the current state."""
		if self.exception:
			return "%s: %s" % (self.state, self.exception)
		return self.state

	def _fetchCallFunc(self, ftpGet):
		"""Called while an image is being downloaded.
		When the download finishes, handle it.
		"""
		if not ftpGet.isDone():
			return
		ftpState = ftpGet.getState()
		if ftpState == FTPGet.Done:
			self.state = _ImSt_Downloaded
		else:
			self.state = _ImSt_DownloadFailed
			self.exception = ftpGet.getException()
		if self.fetchCallFunc:
			self.fetchCallFunc(self)
	
	def __del__(self):
		"""Halt download (if any) and delete object on disk."""
		if not _LocalMode:
			if self.state == _ImSt_Downloaded:
				self.state = _ImSt_FileReadFailed
				self.exception = "deleted"
				locPath = self.getLocalPath()
				if os.path.exists(locPath):
					if _DebugFileDel:
						print "%s deleting %r" % (self, locPath)
					os.remove(locPath)
		elif _DebugFileDel:
			print "%s.__del__; state=%s" % (self.imageName, self.state)
	
	def __str__(self):
		return "%s(%s)" % (self.__class__.__name__, self.imageName)


class ImObj(BasicImObj):
	def __init__(self,
		baseDir,
		imageName,
		cmdChar,
		cmdr,
		cmdID,
		guideModel,
		fetchCallFunc = None,
	):
		self.currCmdChar = cmdChar
		self.currCmdrCmdID = (cmdr, cmdID)
		self.sawStarTypes = []
		self.starDataDict = {}
		self.selDataColor = None
		self.defThresh = None
		self.currThresh = None

		BasicImObj.__init__(self,
			baseDir = baseDir,
			imageName = imageName,
			guideModel = guideModel,
			fetchCallFunc = fetchCallFunc,
		)
		
	
class GuideWdg(Tkinter.Frame):
	def __init__(self,
		master,
		actor,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		self.actor = actor
		self.guideModel = GuideModel.getModel(actor)
		self.tuiModel = TUI.TUIModel.getModel()
		
		self.nToSave = _HistLen # eventually allow user to set?
		self.imObjDict = RO.Alg.ReverseOrderedDict()
		self.maskDict = weakref.WeakValueDictionary() # dictionary of mask name: weak link to imObj data for that mask
		self.dispImObj = None # object data for most recently taken image, or None
		self.inCtrlClick = False
		self.ds9Win = None
		
		self.manGuideScriptRunner = None

		guideStateFrame = Tkinter.Frame(self)
		
		RO.Wdg.StrLabel(
			master = guideStateFrame,
			text = "Guiding",
		).pack(side="left")
		self.guideStateWdg = RO.Wdg.StrLabel(
			master = guideStateFrame,
			formatFunc = str.capitalize,
			helpText = "Current state of guiding",
			helpURL = _HelpPrefix + "GuidingStatus",
		)
		self.guideModel.guiding.addROWdg(self.guideStateWdg)
		self.guideStateWdg.pack(side="left")
		
		guideStateFrame.pack(side="top", anchor="w")
		
		helpURL = _HelpPrefix + "HistoryControls"
		
		histFrame = Tkinter.Frame(self)
		
		self.prevImWdg = RO.Wdg.Button(
			histFrame,
			text = u"\N{WHITE LEFT-POINTING TRIANGLE}",
			callFunc = self.doPrevIm,
			helpText = "Show previous image",
			helpURL = helpURL,
		)
		self.prevImWdg.setEnable(False)
		self.prevImWdg.pack(side="left")
		
		self.nextImWdg = RO.Wdg.Button(
			histFrame,
			text = u"\N{WHITE RIGHT-POINTING TRIANGLE}",
			callFunc = self.doNextIm,
			helpText = "Show next image",
			helpURL = helpURL,
		)
		self.nextImWdg.setEnable(False)
		self.nextImWdg.pack(side="left")
		
		self.showCurrWdg = RO.Wdg.Checkbutton(
			histFrame,
			text = "Current",
			defValue = True,
			callFunc = self.doShowCurr,
			helpText = "Display current image?",
			helpURL = helpURL,
		)
		self.showCurrWdg.pack(side="left")
		
		self.imNameWdg = RO.Wdg.StrLabel(
			master = histFrame,
			anchor="e",
			helpText = "Name of displayed image",
			helpURL = helpURL,
			)
		self.imNameWdg.pack(side="left", expand=True, fill="x", padx=4)
		
		histFrame.pack(side="top", anchor="w", expand=True, fill="x")

		self.gim = GImDisp.GrayImageWdg(self)
		self.gim.pack(side="top", anchor="w", expand=True, fill="both")
		
		self.defCnvCursor = self.gim.cnv["cursor"]
		
		helpURL = _HelpPrefix + "DataPane"
		
		starFrame = Tkinter.Frame(self)

		RO.Wdg.StrLabel(
			starFrame,
			text = " Star ",
			bd = 0,
			padx = 0,
			helpText = "Information about the selected star",
			helpURL = helpURL,
		).pack(side="left")
		
		RO.Wdg.StrLabel(
			starFrame,
			text = "Pos: ",
			bd = 0,
			padx = 0,
			helpText = "Centroid of the selected star (pix)",
			helpURL = helpURL,
		).pack(side="left")
		self.starXPosWdg = RO.Wdg.FloatLabel(
			starFrame,
			width = 6,
			precision = 1,
			anchor="e",
			bd = 0,
			padx = 0,
			helpText = "X centroid of selected star (pix)",
			helpURL = helpURL,
		)
		self.starXPosWdg.pack(side="left")
		
		RO.Wdg.StrLabel(
			starFrame,
			text = ", ",
			bd = 0,
			padx = 0,
		).pack(side="left")
		self.starYPosWdg = RO.Wdg.FloatLabel(
			starFrame,
			width = 6,
			precision = 1,
			anchor="e",
			bd = 0,
			padx = 0,
			helpText = "Y centroid of selected star (pix)",
			helpURL = helpURL,
		)
		self.starYPosWdg.pack(side="left")

		RO.Wdg.StrLabel(
			starFrame,
			text = "  FWHM: ",
			bd = 0,
			padx = 0,
			helpText = "FWHM of selected star (pix)",
			helpURL = helpURL,
		).pack(side="left")
		self.starFWHMWdg = RO.Wdg.FloatLabel(
			starFrame,
			width = 4,
			precision = 1,
			anchor="e",
			bd = 0,
			padx = 0,
			helpText = "FWHM of selected star (ADUs)",
			helpURL = helpURL,
		)
		self.starFWHMWdg.pack(side="left")

		RO.Wdg.StrLabel(
			starFrame,
			text = "  Ampl: ",
			bd = 0,
			padx = 0,
			helpText = "Amplitude of selected star (ADUs)",
			helpURL = helpURL,
		).pack(side="left")
		self.starAmplWdg = RO.Wdg.FloatLabel(
			starFrame,
			width = 7,
			precision = 1,
			anchor="e",
			bd = 0,
			padx = 0,
			helpText = "Amplitude of selected star (ADUs)",
			helpURL = helpURL,
		)
		self.starAmplWdg.pack(side="left")
		
		RO.Wdg.StrLabel(
			starFrame,
			text = "  Bkgnd: ",
			bd = 0,
			padx = 0,
			helpText = "Background level at selected star (ADUs)",
			helpURL = helpURL,
		).pack(side="left")
		self.starBkgndWdg = RO.Wdg.FloatLabel(
			starFrame,
			width = 6,
			precision = 1,
			anchor="e",
			bd = 0,
			padx = 0,
			helpText = "Background level at selected star (ADUs)",
			helpURL = helpURL,
		)
		self.starBkgndWdg.pack(side="left")

		starFrame.pack(side="top", anchor="w")
		
		helpURL = _HelpPrefix + "AcquisitionControls"
		
		inputFrame = Tkinter.Frame(self)

		helpText = "exposure time"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Exp Time",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.expTimeWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = self.guideModel.gcamInfo.minExpTime,
			maxValue = self.guideModel.gcamInfo.maxExpTime,
			defValue = self.guideModel.gcamInfo.defExpTime,
			defFormat = "%.1f",
			defMenu = "Current",
			minMenu = "Minimum",
			autoIsCurrent = True,
			helpText = helpText,
			helpURL = helpURL,
		)
		self.expTimeWdg.pack(side="left")

		RO.Wdg.StrLabel(
			inputFrame,
			text = "sec",
			width = 4,
			anchor = "w",
		).pack(side="left")

		helpText = "binning factor"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Bin",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.binFacWdg = RO.Wdg.IntEntry(
			inputFrame,
			minValue = 1,
			maxValue = 99,
			defValue = self.guideModel.gcamInfo.defBinFac,
			defMenu = "Current",
			autoIsCurrent = True,
			helpText = helpText,
		)
		self.binFacWdg.pack(side="left")
		
		helpText = "threshold for finding stars"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Thresh",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.threshWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = 0,
			defValue = 3.0, # set from hub, once we can!!!
			defFormat = "%.1f",
			defMenu = "Current",
			autoIsCurrent = True,
			width = 5,
			helpText = helpText,
			helpURL = helpURL,
		)
		self.threshWdg.pack(side="left")

		RO.Wdg.StrLabel(
			inputFrame,
			text = u"\N{GREEK SMALL LETTER SIGMA}",
		).pack(side="left")

		inputFrame.pack(side="top", anchor="w")
				
		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			dispatcher = self.tuiModel.dispatcher,
			prefs = self.tuiModel.prefs,
			playCmdSounds = True,
			helpURL = _HelpPrefix + "StatusBar",
		)
		self.statusBar.pack(side="top", anchor="w", expand=True, fill="x")
		
		self.devSpecificFrame = Tkinter.Frame(self)
		self.devSpecificFrame.pack(side="top", anchor="w", expand=True, fill="x")
		
		helpURL = _HelpPrefix + "GuidingControls"
		
		cmdButtonFrame = Tkinter.Frame(self)

		self.exposeBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Expose",
			callFunc = self.doExpose,
			helpText = "Take an exposure",
			helpURL = helpURL,
		)
		self.exposeBtn.pack(side="left")
		
		self.centerBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Center",
			callFunc = self.doCenterOnSel,
			helpText = "Put selected star on the boresight",
			helpURL = helpURL,
		)
		if self.guideModel.gcamInfo.slitViewer:
			self.centerBtn.pack(side="left")
		
		self.manGuideBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Man Guide",
			callFunc = self.doManGuide,
			helpText = "Expose repeatedly; use ctrl-click to center",
			helpURL = helpURL,
		)
		if self.guideModel.gcamInfo.slitViewer:
			self.manGuideBtn.pack(side="left")

		self.guideOnBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Guide",
			callFunc = self.doGuideOn,
			helpText = "Start guiding on selected star",
			helpURL = helpURL,
		)
		self.guideOnBtn.pack(side="left")
		
		self.guideOnBoresightBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Guide Boresight",
			callFunc = self.doGuideOnBoresight,
			helpText = "Guide on whatever is at the boresight",
			helpURL = helpURL,
		)
		if self.guideModel.gcamInfo.slitViewer:
			self.guideOnBoresightBtn.pack(side="left")
		
		self.guideOffBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Stop Guiding",
			callFunc = self.doGuideOff,
			helpText = "Turn off guiding",
			helpURL = helpURL,
		)
		self.guideOffBtn.pack(side="left")
		
		Tkinter.Label(cmdButtonFrame, text=" ").pack(side="right")
		
		self.ds9Btn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "DS9",
			callFunc = self.doDS9,
			helpText = "Display image in ds9",
			helpURL = helpURL,
		)
		self.ds9Btn.pack(side="right")

		cmdButtonFrame.pack(side="top", anchor="w", expand=True, fill="x")
		
		# disable centroid and guide buttons (no star selected)
		self.guideOnBtn.setEnable(True)
		
		# event bindings
		self.gim.cnv.bind("<Button-1>", self.dragStart, add=True)
		self.gim.cnv.bind("<B1-Motion>", self.dragContinue, add=True)
		self.gim.cnv.bind("<ButtonRelease-1>", self.dragEnd, add=True)
		self.gim.cnv.bind("<Control-Button-1>", self.doCenterOnClick)
		
		self.threshWdg.bind("<FocusOut>", self.doFindStars)
		self.threshWdg.bind("<Return>", self.doFindStars)
		
		# keyword variable bindings
		self.guideModel.fsActThresh.addIndexedCallback(self.updThresh)
		self.guideModel.files.addCallback(self.updFiles)
		self.guideModel.star.addCallback(self.updStar)

		# bindings to set the image cursor
		tl = self.winfo_toplevel()
		tl.bind("<Control-KeyPress>", self.cursorCtr, add=True)
		tl.bind("<Control-KeyRelease>", self.ignoreEvt, add=True)
		tl.bind("<KeyRelease>", self.cursorNormal, add=True)
		
		# exit handler
		atexit.register(self._exitHandler)
	
	def cursorCtr(self, evt=None):
		"""Show image cursor for "center on this point".
		"""
		self.gim.cnv["cursor"] = "crosshair"
	
	def cursorNormal(self, evt=None):
		"""Show normal image cursor.
		"""
		self.gim.cnv["cursor"] = self.defCnvCursor
	
	def doCenterOnClick(self, evt):
		"""Center up on the command-clicked image location.
		"""
		self.inCtrlClick = True
		
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return
	
		if not self.guideModel.gcamInfo.slitViewer:
			self.statusBar.setMsg("Ctrl-click requires a slit viewer", severity = RO.Constants.sevWarning)
			return
	
		if self.gim.mode != "normal": # recode to use a class constant
			self.statusBar.setMsg("Ctrl-click requires a select mode", severity = RO.Constants.sevWarning)
			return
		
		cnvPos = self.gim.cnvPosFromEvt(evt)
		imPos = self.gim.imPosFromCnvPos(cnvPos)
		
		cmdStr = "guide on imgFile=%r centerOn=%.2f,%.2f noGuide %s" % \
			(self.dispImObj.imageName, imPos[0], imPos[1], self.getExpArgStr())
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
	
	def doCenterOnSel(self, evt):
		"""Center up on the selected star.
		"""
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return
		if not self.dispImObj.selDataColor:
			self.statusBar.setMsg("No star selected", severity = RO.Constants.sevWarning)
			return
		
		starData, color = self.dispImObj.selDataColor
		pos = starData[2:4]
		cmdStr = "guide on imgFile=%r centerOn=%.2f,%.2f noGuide %s" % \
			(self.dispImObj.imageName, pos[0], pos[1], self.getExpArgStr()
		)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
	
	def doExistingImage(self, imageName, cmdChar, cmdr, cmdID):
		"""Data is about to arrive for an existing image.
		Decide whether we are interested in it,
		and if so, get ready to receive it.
		"""
		#print "doExistingImage(imageName=%r, cmdChar=%r, cmdr=%r, cmdID=%r" % (imageName, cmdChar, cmdr, cmdID)
		# see if this data is of interest
		imObj = self.imObjDict.get(imageName)
		if not imObj:
			# I have no knowledge of this image, so ignore the data
			return
		isMe = (cmdr == self.tuiModel.getCmdr())
		if not isMe:
			# I didn't trigger this command, so ignore the data
			return
		
		# data is of interest; update cmdr and cmdID
		# and clear sawStarTypes
		imObj.currCmdChar = cmdChar
		imObj.currCmdrCmdID = (cmdr, cmdID)
		imObj.sawStarTypes = []
	
	def doDS9(self, wdg=None):
		"""Display the current image in ds9.
		
		Warning: will need updating once user can display mask;
		lord knows what it'll need once user can display mask*data!
		"""
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return

		# open ds9 window if necessary
		if self.ds9Win:
			# reopen window if necessary
			self.ds9Win.doOpen()
		else:
			self.ds9Win = RO.DS9.DS9Win(self.actor)
		
		localPath = self.dispImObj.getLocalPath()
		self.ds9Win.showFITSFile(localPath)		

	def doExpose(self, wdg=None):
		"""Take an exposure.
		"""
		cmdStr = "findstars " + self.getExpArgStr(inclThresh=True)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
		
	def doFindStars(self, *args):
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return

		thresh = self.threshWdg.getNum()
		if thresh == self.dispImObj.currThresh:
			return
		
		# not strictly necessary since the hub will return this data;
		# still, it is safer to set it now and be sure it gets set
		self.dispImObj.currThresh = thresh
		
		# execute new command
		cmdStr = "findstars file=%r thresh=%s" % (self.dispImObj.imageName, thresh)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
			GuideTest.findStars(self.dispImObj.imageName, thresh = thresh)
	
	def doGuideOff(self, wdg=None):
		"""Turn off guiding.
		"""
		sr = self.manGuideScriptRunner
		if sr and sr.isExecuting():
			sr.cancel()
		else:
			cmdStr = "guide off"
			if not _LocalMode:
				cmdVar = RO.KeyVariable.CmdVar(
					actor = self.actor,
					cmdStr = cmdStr,
				)
				self.statusBar.doCmd(cmdVar)
			else:
				print cmdStr
	
	def doGuideOn(self, wdg=None):
		"""Guide on the selected star.
		"""
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return
		if not self.dispImObj.selDataColor:
			self.statusBar.setMsg("No star selected", severity = RO.Constants.sevWarning)
			return
		
		starData, color = self.dispImObj.selDataColor
		pos = starData[2:4]
		rad = starData[6]
		cmdStr = "guide on imgFile=%r gstar=%.2f,%.2f cradius=%.1f %s" % \
			(self.dispImObj.imageName, pos[0], pos[1], rad, self.getExpArgStr()
		)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
	
	def doGuideOnBoresight(self, wdg=None):
		"""Guide on boresight.
		"""
		cmdStr = "guide on boresight %s" % (self.getExpArgStr())
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
	
	def doManGuide(self, wdg=None):
		"""Repeatedly expose. Let the user control-click to center up.
		"""
		cmdStr = "findstars " + self.getExpArgStr(inclThresh=True)
		def guideScript(sr, cmdStr=cmdStr):
			# disable Expose, Guide, etc.
			
			# take exposures forever
			while True:
				yield sr.waitCmd(cmdStr)

		self.manGuideScriptRunner = RO.ScriptRunner.ScriptRunner(
			master = self,
			name = "Manual guide script",
			dispatcher = self.tuiModel.dispatcher,
			runFunc = guideScript,
			cmdStatusBar = self.statusBar,
			startNow = True
		)
	
	def doNextIm(self, wdg=None):
		"""Show next image from history list"""
		revHist, currInd = self.getHistInfo()
		if currInd == None:
			self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevWarning)
			return

		if currInd > 0:
			nextImObj = revHist[currInd-1]
		else:
			self.statusBar.setMsg("Showing newest image", severity = RO.Constants.sevWarning)
			return
		
		self.showImage(nextImObj)
	
	def doPrevIm(self, wdg=None):
		"""Show previous image from history list"""
		self.showCurrWdg.setBool(False)

		revHist, currInd = self.getHistInfo()
		if currInd == None:
			self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevWarning)
			return

		try:
			prevImObj = revHist[currInd+1]
		except IndexError:
			self.statusBar.setMsg("Showing oldest image", severity = RO.Constants.sevWarning)
			return
		
		self.showImage(prevImObj)
			
	def doSelect(self, evt):
		"""Select a star based on a mouse click
		- If near a found star, select it
		- Otherwise centroid at that point and select the result (if successful)
		"""
		if not self.gim.isNormalMode():
			return
		cnvPos = self.gim.cnvPosFromEvt(evt)
		imPos = self.gim.imPosFromCnvPos(cnvPos)

		try:
			# get current image object
			if not self.dispImObj:
				return
			
			# erase data for now (helps for early return)
			self.dispImObj.selDataColor = None
	
			# look for nearby centroid to choose
			selStarData = None
			minDistSq = _MaxDist
			for typeChar, starDataList in self.dispImObj.starDataDict.iteritems():
				#print "doSelect checking typeChar=%r, nstars=%r" % (typeChar, len(starDataList))
				tag, color = _TypeTagColorDict[typeChar]
				for starData in starDataList:
					distSq = (starData[2] - imPos[0])**2 + (starData[3] - imPos[1])**2
					if distSq < minDistSq:
						minDistSq = distSq
						selStarData = starData
						selColor = color
	
			if selStarData:
				self.dispImObj.selDataColor = (selStarData, selColor)
		finally:
			# update display
			self.showSelection()
	
	def doShowCurr(self, wdg=None):
		imObj = None
		if self.showCurrWdg.getBool():
			# show most recent downloaded image
			revHist = self.imObjDict.values()
			for imObj in revHist:
				if imObj.state == _ImSt_Downloaded:
					break
			else:
				# there are no current images
				self.gim.clear()
				imObj = None
			
			if imObj == self.dispImObj:
				# image is already being displayed
				imObj = None
				
		if imObj:
			self.showImage(imObj)
		else:
			self.enableHist()
		
	def dragStart(self, evt):
		"""Mouse down for current drag (whatever that might be).
		"""
		if not self.gim.isNormalMode():
			return
		self.dragStart = self.gim.cnvPosFromEvt(evt)
		self.dragRect = self.gim.cnv.create_rectangle(
			self.dragStart[0], self.dragStart[1], self.dragStart[0], self.dragStart[1],
			outline = _CentroidColor,
			tags = _DragRectTag,
		)
	
	def dragContinue(self, evt):
		if self.inCtrlClick:
			return
		if not self.gim.isNormalMode():
			return
		newPos = self.gim.cnvPosFromEvt(evt)
		self.gim.cnv.coords(self.dragRect, self.dragStart[0], self.dragStart[1], newPos[0], newPos[1])
	
	def dragEnd(self, evt):
		if self.inCtrlClick:
			self.inCtrlClick = False
			return

		if not self.gim.isNormalMode():
			return

		endPos = self.gim.cnvPosFromEvt(evt)
		startPos = self.dragStart or endPos

		self.gim.cnv.delete(_DragRectTag)
		self.dragStart = None
		self.dragRect = None
		
		if not self.dispImObj:
			return

		meanPos = num.divide(num.add(startPos, endPos), 2.0)
		deltaPos = num.subtract(endPos, startPos)

		rad = max(deltaPos) / (self.gim.zoomFac * 2.0)
		imPos = self.gim.imPosFromCnvPos(meanPos)
		
		if abs(deltaPos[0]) > 1 and abs(deltaPos[1] > 1):
			# centroid

			# execute centroid command
			cmdStr = "centroid file=%r on=%s,%s radius=%s" % (self.dispImObj.imageName, imPos[0], imPos[1], rad)
			if not _LocalMode:
				cmdVar = RO.KeyVariable.CmdVar(
					actor = self.actor,
					cmdStr = cmdStr,
				)
				self.statusBar.doCmd(cmdVar)
			else:
				print cmdStr
				GuideTest.centroid(self.dispImObj.imageName, on=imPos, rad=rad)
			
		else:
			# select
			self.doSelect(evt)
	
	def enableHist(self):
		"""Set enable of prev and next buttons"""
		if self.showCurrWdg.getBool():
			self.prevImWdg.setEnable(False)
			self.nextImWdg.setEnable(False)
		else:
			revHist, currInd = self.getHistInfo()
			isOldest = True
			isNewest = True
	
			if (len(revHist) > 0) and (currInd != None):
				if currInd >= len(revHist) - 1:
					isOldest = True
					
				if (currInd <= 0):
					isNewest = True
		
			self.prevImWdg.setEnable(not isOldest)
			self.nextImWdg.setEnable(not isNewest)
		
	def fetchCallback(self, imObj):
		"""Called when an image is finished downloading.
		"""
		if self.showCurrWdg.getBool():
			self.showImage(imObj)
	
	def getExpArgStr(self, inclThresh = False):
		"""Return exposure time and bin factor exposure arguments
		as a string suitable for a guide camera command.
		"""
		argList = []
		expTimeStr = self.expTimeWdg.getString()
		if expTimeStr:
			argList.append("exptime=" + expTimeStr)

		binFacStr = self.binFacWdg.getString()
		if binFacStr:
			argList.append("bin=" + binFacStr)
		
		if inclThresh:
			threshStr = self.threshWdg.getString()
			if threshStr:
				argList.append("thresh=" + threshStr)
		
		return " ".join(argList)
	
	def getHistInfo(self):
		"""Return information about the location of the current image in history.
		Returns:
		- revHist: list of image objects in history in reverse order (most recent first)
		- currImInd: index of displayed image in history
		  or None if no image is displayed or displayed image not in history at all
		"""
		revHist = self.imObjDict.values()
		try:
			currImInd = revHist.index(self.dispImObj)
		except (ValueError, IndexError):
			currImInd = None
		return (revHist, currImInd)

		try:
			nextImObj = imList[currInd+1]
		except indexError:
			nextImObj = None
		isCurrent = (nextImObj == None)
			
		nextImObj = imList[currInd+1]
		return (isCurr, prevImObj, nextImObj)
	
	def ignoreEvt(self, evt=None):
		pass
	
	def showImage(self, imObj):
		"""Display an image.
		"""
		#print "showImage(imObj=%s)" % (imObj,)
		fitsIm = imObj.getFITSObj()
		if not fitsIm:
			if imObj.state in (_ImSt_DownloadFailed, _ImSt_FileReadFailed):
				sev = RO.Constants.sevError
			else:
				sev = RO.Constants.sevWarning
			self.statusBar.setMsg("Image %r: %s" % (imObj.imageName, imObj.getStatesStr()), sev)
			imArr = None
			expTime = None
			binFac = None
		else:
			imArr = fitsIm[0].data
			imHdr = fitsIm[0].header
			expTime = imHdr.get("EXPTIME")
			binFac = imHdr.get("BINX")
	
		# display new data
		self.gim.showArr(imArr)
		self.dispImObj = imObj
		self.imNameWdg["text"] = imObj.imageName
		self.expTimeWdg.set(expTime)
		self.expTimeWdg.setDefault(expTime)
		self.binFacWdg.set(binFac)
		self.binFacWdg.setDefault(binFac)
		self.threshWdg.setDefault(imObj.defThresh)
		self.threshWdg.set(imObj.currThresh)
		
		self.enableHist()
		
		if imArr != None:
			# add existing annotations, if any and show selection
			# (for now just display them,
			# but eventually have a control that can show/hide them,
			# and -- as the first step -- set the visibility of the tags appropriately)
			for cmdChar, starDataList in imObj.starDataDict.iteritems():
				for starData in starDataList:
					tag, color = _TypeTagColorDict[cmdChar]
					self.gim.addAnnotation(
						GImDisp.ann_Circle,
						imPos = starData[2:4],
						rad = starData[6],
						isImSize = True,
						tags = tag,
						outline = color,
					)
			
			self.showSelection()

	def showSelection(self):
		"""Display the current selection.
		"""
		# clear current selection
		self.gim.removeAnnotation(_SelTag)

		if not self.dispImObj or not self.dispImObj.selDataColor:
			# disable controls
			self.guideOnBtn.setEnable(False)
			
			# clear data display
			self.starXPosWdg.set(None)
			self.starYPosWdg.set(None)
			self.starFWHMWdg.set(None)
			self.starAmplWdg.set(None)
			self.starBkgndWdg.set(None)
			
			return
		
		starData, color = self.dispImObj.selDataColor

		# draw selection
		selID = self.gim.addAnnotation(
			GImDisp.ann_X,
			imPos = starData[2:4],
			isImSize = False,
			rad = _MarkRad,
			holeRad = _HoleRad,
			tags = _SelTag,
			fill = color,
		)
		
		# update data display
		self.starXPosWdg.set(starData[2])
		self.starYPosWdg.set(starData[3])
		fwhm = (starData[8] + starData[9]) / 2.0
		self.starFWHMWdg.set(fwhm)
		self.starAmplWdg.set(starData[14])
		self.starBkgndWdg.set(starData[13])
	
		# enable controls
		self.guideOnBtn.setEnable(True)
		
	def updFiles(self, fileData, isCurrent, keyVar):
		#print "%s updFiles(fileData=%r; isCurrent=%r)" % (self.actor, fileData, isCurrent)
		if not isCurrent:
			return
		
		cmdChar, isNew, baseDir, imageName, maskName = fileData[0:5]
		msgDict = keyVar.getMsgDict()
		cmdr = msgDict["cmdr"]
		cmdID = msgDict["cmdID"]
		imageName = baseDir + imageName
		if maskName:
			maskName = baseDir + maskName

		if not isNew:
			# handle data for existing image
			self.doExistingImage(imageName, cmdChar, cmdr, cmdID)
			return
		
		# at this point we know we have a new image
		
		if not self.winfo_exists() and self.winfo_ismapped():
			# window is not visible; do NOT download files
			# wait until we know it's a new image to test for this
			# because if we have downloaded a file
			# then we should record the data that goes with it
			self.dispImObj = None
			return				
		
		# create new object data
		baseDir = self.guideModel.ftpSaveToPref.getValue()
		msgDict = keyVar.getMsgDict()
		cmdr = msgDict["cmdr"]
		cmdID = msgDict["cmdID"]
		imObj = ImObj(
			baseDir = baseDir,
			imageName = imageName,
			cmdChar = cmdChar,
			cmdr = cmdr,
			cmdID = cmdID,
			guideModel = self.guideModel,
			fetchCallFunc = self.fetchCallback,
		)
		self.imObjDict[imObj.imageName] = imObj
		imObj.fetchFile()

		# associate mask data, creating it if necessary
		if maskName:
			maskObj = self.maskDict.get(maskName)
			if not maskObj:
				maskObj = BasicImObj(
					baseDir = baseDir,
					imageName = maskName,
					guideModel = self.guideModel,
				)
				self.maskDict[maskName] = maskObj
			imObj.maskObj = maskObj

		# purge excess images
		if len(self.imObjDict) > self.nToSave:
			keys = self.imObjDict.keys()
			for imName in keys[self.nToSave:]:
				del(self.imObjDict[imName])

	def updStar(self, starData, isCurrent, keyVar):
		"""New star data found.
		
		Overwrite existing findStars data if:
		- No existing data and cmdr, cmdID match
		- I generated the command
		else ignore.
		
		Replace existing centroid data if I generated the command,
		else ignore.
		"""
		#print "%s updStar(starData=%r, isCurrent=%r)" % (self.actor, starData, isCurrent)
		if not isCurrent:
			return

		# get image object (ignore if no match)
		msgDict = keyVar.getMsgDict()
		cmdrCmdID = (msgDict["cmdr"], msgDict["cmdID"])
		for imObj in self.imObjDict.itervalues():
			if cmdrCmdID == imObj.currCmdrCmdID:
				break
		else:
			return
		
		isVisible = (self.dispImObj and self.dispImObj.imageName == imObj.imageName)
		typeChar = starData[0]
		try:
			tag, color = _TypeTagColorDict[typeChar]
		except KeyError:
			raise RuntimeError("Unknown type character %r for star data" % (typeChar,))

		updSel = False
		if typeChar in imObj.sawStarTypes:
			# add star data
			imObj.starDataDict[typeChar].append(starData)
		else:	
			# first star data of this type seen for this command;
			# update selection if necessary and restart this type of data
			if not imObj.sawStarTypes:
				# first star data of ANY type seen for this command; reset selection
				imObj.selDataColor = (starData, color)
				updSel = True

			# reset this type of data
			imObj.starDataDict[typeChar] = [starData]
			imObj.sawStarTypes.append(typeChar)

			if isVisible:
				self.gim.removeAnnotation(tag)

		if not isVisible:
			# this image is not being displayed, so we're done
			return
		
		# update the display
		self.gim.addAnnotation(
			GImDisp.ann_Circle,
			imPos = starData[2:4],
			rad = starData[6],
			isImSize = True,
			tags = tag,
			outline = color,
		)
		
		# if this star was selected, display selection
		if updSel:
			self.showSelection()

	def updThresh(self, thresh, isCurrent, keyVar):
		"""New threshold data found.
		"""
		#print "%s updThresh(thresh=%r, isCurrent=%r)" % (self.actor, thresh, isCurrent)
		if not isCurrent:
			return

		# get image object (ignore if no match)
		msgDict = keyVar.getMsgDict()
		cmdrCmdID = (msgDict["cmdr"], msgDict["cmdID"])
		for imObj in self.imObjDict.itervalues():
			if cmdrCmdID == imObj.currCmdrCmdID:
				break
		else:
			return
		
		if imObj.currThresh == None:
			imObj.defThresh = thresh
		imObj.currThresh = thresh

		isVisible = (self.dispImObj and self.dispImObj.imageName == imObj.imageName)
		if isVisible:
			self.threshWdg.setDefault(imObj.defThresh)
			self.threshWdg.set(imObj.currThresh)
	
	def _exitHandler(self):
		"""Delete all image files and mask files.
		"""
		for maskObj in self.maskDict.itervalues():
			maskObj.__del__()
		for imObj in self.imObjDict.itervalues():
			imObj.__del__()


if __name__ == "__main__":
	_LocalMode = True

	root = RO.Wdg.PythonTk()

	GuideTest.init()	

	testFrame = GuideWdg(root, "ecam")
	testFrame.pack(expand="yes", fill="both")

	GuideTest.run()

	root.mainloop()


