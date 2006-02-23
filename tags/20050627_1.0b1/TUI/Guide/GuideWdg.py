#!/usr/local/bin/python
"""Guiding support

To do:
- Record all guiding params with the guide image (using a dictionary, perhaps?).
  Trying to get them from FITS headers is not ideal when users may be trying
  to avoid downloading images -- though it's also no big deal if they're planning
  to CHANGE those params since they probably should see the image first.
- Try to rationalize and centralize the code that sets the guide param entry widgets.
  This will be much easier if imObj contains all the info (rather than the fits header).
  
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
					Added _DebugMem flag and commented out the remaining
					non-flag-protected diagnostic print statement.
2005-05-20 ROwen	Bug fix: was not setting ImObj.defThresh on creation.
					But fix: set ImObj.currThresh to None instead of default if curr thresh unknown.
					Bug fix: layout was messed up by going to the packer so reverted to gridder.
					(The space for multiple widgets with expand=True is always shared
					even if some of them only grow in one direction. Truly hideous!)
					Bug fix: the history controls were always disabled.
2005-05-23 ROwen	Mod. to overwrite image files if new ones come in with the same name;
					this simplifies debugging and corrects bugs associated with the old way
					(the new image's ImObj would replace the old one, so the old one
					was never accessible and never deleted).
					Bug fix: typo in code that handled displaying unavailable images.
2005-05-26 ROwen	Cleaned up button enable/disable.
					Added doCmd method to centralize command execution.
2005-06-09 ROwen	Added more _DebugMem output.
					Apparently fixed a bug that prevented file delete for too-old files.
2005-06-10 ROwen	Modified for noStarsFound->noGuideStar in guide model.
					Also changed the no stars message to "Star Not Found".
2005-06-13 ROwen	Bug fix: one of the delete delete messages was mis-formatted.
					Added more memory tracking code.
					Modified test code to download images from APO.
2005-06-15 ROwen	Added Choose... button to open any fits file.
					Modified so displayed image is always in history list;
					also if there is a gap then the history buttons show it.
2005-06-16 ROwen	Changed to not use a command status bar for manual guiding.
					Modified updGuideState to use new KeyVar getSeverity method.
					Modified to only import GuideTest if in test mode.
					Bug fix: isGuiding usually returned False even if true.
					Bug fix: dragStar used as method name and attribute (found by pychecker).
2005-06-17 ROwen	Bug fix: mis-handled Cancel in Choose... dialog.
					Bug fix: pyfits.open can return [] for certain kinds of invalid image files,
					instead of raising an exception (presumably a bug in pyfits).
					This case is now handled properly.
					Manual centroid was sending radius instead of cradius.
2005-06-21 ROwen	Overhauled command buttons: improved layout and better names.
					Removed the Center button (use control-click).
					Changed appearance of the "Current" button to make it clearer.
					Moved guiding status down to just above the status bar.
2005-06-22 ROwen	Moved guiding status back to the top.
					Changed display of current image name to a read-only entry; this fixed
					a resize problem and allows the user to scroll to see the whole name.
2005-06-23 ROwen	Added logic to disable the currently active command button.
					Added a Cancel button to re-enable buttons when things get stuck.
					Improved operation while guide window closed: image info
					is now kept in the history as normal, but download is deferred
					until the user displays the guide window and tries to look at an image.
					Images that cannot be displayed now show the reason
					in the middle of the image area, instead of in the status bar.
					Tweaked definition of isGuiding to better match command enable;
					now only "off" is not guiding; formerly "stopping" was also not guiding.
2005-06-24 ROwen	Modified to use new hub manual guider.
					Added show/hide Image button.
					Modified the way exposure parameters are updated: now they auto-track
					the current value if they are already current. But as soon as you
					change one, the change sticks. This is in preparation for
					support of guiding tweaks.
					Modified to not allow guiding on a star from a non-current image
					(if the guider is ever smart enough to invalidate images
					once the telescope has moved, this can be handled more flexibly).
					Bug fix in test code; GuideTest not setting _LocalMode.
					Bug fix: current image name not right-justified after shrinking window.
2005-06-27 ROwen	Removed image show/hide widget for now; I want to straighten out
					the resize behavior and which other widgets to hide or disable
					before re-enabling this feature.
"""
import atexit
import os
import sys
import weakref
import Tkinter
import tkFileDialog
import numarray as num
import pyfits
import RO.Alg
import RO.CanvasUtil
import RO.Constants
import RO.Comm.FTPGet as FTPGet
import RO.DS9
import RO.KeyVariable
import RO.OS
import RO.Wdg
import RO.Wdg.GrayImageDispWdg as GImDisp
import TUI.TUIModel
import GuideModel

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
_DebugMem = False # print a message when a file is deleted from disk?


class BasicImObj(object):
	StReady = "Ready to download"
	StDownloading = "Downloading"
	StDownloaded = "Downloaded"
	StFileReadFailed = "Cannot read file"
	StDownloadFailed = "Download failed"
	StExpired = "Expired; file deleted"

	def __init__(self,
		baseDir,
		imageName,
		guideModel,
		fetchCallFunc = None,
		isLocal = False,
	):
		self.baseDir = baseDir
		self.imageName = imageName
		self.maskObj = None
		self.guideModel = guideModel
		self.exception = None
		self.fetchCallFunc = fetchCallFunc
		self.isLocal = isLocal or _LocalMode
		if not self.isLocal:
			self.state = self.StReady
		else:
			self.state = self.StDownloaded
		self.isInSequence = not isLocal
	
	def didFail(self):
		"""Return False if download failed or image expired"""
		return self.state in (
			self.StFileReadFailed,
			self.StDownloadFailed,
			self.StExpired,
		)

	def fetchFile(self):
		"""Start downloading the file."""
		#print "%s fetchFile; isLocal=%s" % (self, self.isLocal)
		if self.isLocal:
			self.state = self.StDownloaded
			self._doCallback()
			return

		(host, rootDir), isCurr = self.guideModel.imageRoot.get()
		if None in (host, rootDir):
			self.state = self.StDownloadFailed
			self.exception = "server info (imageRoot) not yet known"
			self._doCallback()
			return

		self.state = self.StDownloading

		# do NOT use os.path to join remote host path components;
		# simply concatenate instead
		fromPath = rootDir + self.imageName

		toPath = self.getLocalPath()
		
		self.guideModel.ftpLogWdg.getFile(
			host = host,
			fromPath = fromPath,
			toPath = toPath,
			isBinary = True,
			overwrite = True,
			createDir = True,
			callFunc = self._fetchCallFunc,
			dispStr = self.imageName,
			username = "images",
			password = "7nights."
		)
	
	def getFITSObj(self):
		"""If the file is available, return a pyfits object,
		else return None.
		"""
		if self.state == self.StDownloaded:
			try:
				fitsIm = pyfits.open(self.getLocalPath())
				if fitsIm:
					return fitsIm
				
				self.state = self.StFileReadFailed
				self.exception = "No image data found"
				return None
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				self.state = self.StFileReadFailed
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

	def isDone(self):
		"""Return True if image file available"""
		return self.state == self.StDownloaded

	def _fetchCallFunc(self, ftpGet):
		"""Called while an image is being downloaded.
		When the download finishes, handle it.
		"""
		if not ftpGet.isDone():
			return
		ftpState = ftpGet.getState()
		if ftpState == FTPGet.Done:
			self.state = self.StDownloaded
		else:
			self.state = self.StDownloadFailed
			self.exception = ftpGet.getException()
			#print "%s download failed: %s" % (self, self.exception)
		self._doCallback()
	
	def _doCallback(self):
		if self.fetchCallFunc:
			self.fetchCallFunc(self)
		if self.isDone():
			self.fetchCallFunc = None
	
	def expire(self):
		"""Delete the file from disk and set state to expired.
		"""
		self.maskObj = None
		if self.isLocal:
			if _DebugMem:
				print "Would delete %r, but is local" % (self.imageName,)
			return
		if self.state == self.StDownloaded:
			self.state = self.StExpired
			locPath = self.getLocalPath()
			if os.path.exists(locPath):
				if _DebugMem:
					print "Deleting %r" % (locPath,)
				os.remove(locPath)
			elif _DebugMem:
				print "Would delete %r, but not found on disk" % (self.imageName,)
		elif _DebugMem:
			print "Would delete %r, but state = %r is not 'downloaded'" % (self.imageName, self.state,)
	
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
		defRadMult = None,
		defThresh = None,
		isLocal = False,
	):
		self.currCmdChar = cmdChar
		self.currCmdrCmdID = (cmdr, cmdID)
		self.sawStarTypes = []
		self.starDataDict = {}
		self.selDataColor = None
		self.defRadMult = defRadMult
		self.defThresh = defThresh
		self.currRadMult = None
		self.currThresh = None

		BasicImObj.__init__(self,
			baseDir = baseDir,
			imageName = imageName,
			guideModel = guideModel,
			fetchCallFunc = fetchCallFunc,
			isLocal = isLocal,
		)


class HistoryBtn(RO.Wdg.Button):
	_InfoDict = {
		(False, False): ("show previous image", u"\N{BLACK LEFT-POINTING TRIANGLE}"),
		(False, True):  ("show previous OUT OF SEQUENCE image", u"\N{WHITE LEFT-POINTING TRIANGLE}"),
		(True,  False): ("show next image", u"\N{BLACK RIGHT-POINTING TRIANGLE}"),
		(True,  True):  ("show next OUT OF SEQUENCE image", u"\N{WHITE RIGHT-POINTING TRIANGLE}"),
	}
	def __init__(self,
		master,
		isNext = True,
	**kargs):
		self.isNext = bool(isNext)
		self.isGap = False
		if self.isNext:
			self.descr = "next"
		else:
			self.descr = "previous"
		RO.Wdg.Button.__init__(self, master, **kargs)
		self._redisplay()
	
	def setState(self, doEnable, isGap):
		self.setEnable(doEnable)
		if self.isGap == bool(isGap):
			return
		self.isGap = bool(isGap)
		self._redisplay()
	
	def _redisplay(self):
		self.helpText, btnText = self._InfoDict[(self.isNext, self.isGap)]
		self["text"] = btnText


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
		self._memDebugDict = {}
		self.maskDict = weakref.WeakValueDictionary() # dictionary of mask name: weak link to imObj data for that mask
		self.dispImObj = None # object data for most recently taken image, or None
		self.inCtrlClick = False
		self.ds9Win = None
		
		self.doingCmd = None # (cmdVar, cmdButton, isGuideOn) used for currently executing cmd
		self._btnsLaidOut = False

		row=0

		guideStateFrame = Tkinter.Frame(self)
		
		RO.Wdg.StrLabel(
			master = guideStateFrame,
			text = "Guiding:",
		).pack(side="left")
		self.guideStateWdg = RO.Wdg.StrLabel(
			master = guideStateFrame,
			formatFunc = str.capitalize,
			anchor = "w",
			helpText = "Current state of guiding",
			helpURL = _HelpPrefix + "GuidingStatus",
		)
		self.guideStateWdg.pack(side="left")
		
		guideStateFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		helpURL = _HelpPrefix + "HistoryControls"
		
		histFrame = Tkinter.Frame(self)
		
		self.showHideImageWdg = RO.Wdg.Checkbutton(
			histFrame,
			text = "Image",
			#onvalue = "Hide",
			#offvalue = "Show",
			#showValue = True,
			#width = 4,
			indicatoron = False,
			defValue = True,
			callFunc = self.doShowHideImage,
			helpText = "Show or hide image",
			helpURL = helpURL,
		)
		#self.showHideImageWdg.pack(side="left")
		
		self.prevImWdg = HistoryBtn(
			histFrame,
			isNext = False,
			callFunc = self.doPrevIm,
			helpURL = helpURL,
		)
		self.prevImWdg.pack(side="left")
		
		self.nextImWdg = HistoryBtn(
			histFrame,
			isNext = True,
			callFunc = self.doNextIm,
			helpURL = helpURL,
		)
		self.nextImWdg.pack(side="left")
		
		onOffVals = ("Current", "Hold")
		lens = [len(val) for val in onOffVals]
		maxLen = max(lens)
		self.showCurrWdg = RO.Wdg.Checkbutton(
			histFrame,
#			text = "Current",
			defValue = True,
			onvalue = onOffVals[0],
			offvalue = onOffVals[1],
			width = maxLen,
			showValue = True,
			callFunc = self.doShowCurr,
			helpText = "Display current image?",
			helpURL = helpURL,
		)
		self.showCurrWdg.pack(side="left")
		
		self.chooseImWdg = RO.Wdg.Button(
			histFrame,
			text = "Choose...",
			callFunc = self.doChooseIm,
			helpText = "Choose a fits file to display",
			helpURL = helpURL,
		)
		self.chooseImWdg.pack(side="right")
		
		self.imNameWdg = RO.Wdg.StrEntry(
			master = histFrame,
			justify="right",
			readOnly = True,
			helpText = "Name of displayed image",
			helpURL = helpURL,
			)
		self.imNameWdg.pack(side="left", expand=True, fill="x", padx=4)
		
		def showRight(evt=None):
			self.imNameWdg.xview("end")
		self.imNameWdg.bind("<Configure>", showRight)
		
		histFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		self.gim = GImDisp.GrayImageWdg(self, helpURL = _HelpPrefix + "Image")
		self.gim.grid(row=row, column=0, sticky="news")
		self.grid_rowconfigure(row, weight=1)
		self.grid_columnconfigure(0, weight=1)
		row += 1
		
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

		starFrame.grid(row=row, column=0, sticky="ew")
		row += 1
		
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
		
		helpText = "radius multipler for finding stars"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "RadMult",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.radMultWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = 0.5,
			defValue = 1.0, # set from hub, once we can!!!
			defFormat = "%.1f",
			defMenu = "Current",
			autoIsCurrent = True,
			width = 5,
			helpText = helpText,
			helpURL = helpURL,
		)
		self.radMultWdg.pack(side="left")

		inputFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		self.devSpecificFrame = Tkinter.Frame(self)
		self.devSpecificFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			dispatcher = self.tuiModel.dispatcher,
			prefs = self.tuiModel.prefs,
			playCmdSounds = True,
			helpURL = _HelpPrefix + "StatusBar",
		)
		self.statusBar.grid(row=row, column=0, sticky="ew")
		row += 1
		
		helpURL = _HelpPrefix + "GuidingControls"
		
		cmdButtonFrame = Tkinter.Frame(self)

		self.exposeBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Expose",
			callFunc = self.doExpose,
			helpText = "Take an exposure",
			helpURL = helpURL,
		)
		
		self.centerBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Center",
			callFunc = self.doCenterOnSel,
			helpText = "Put selected star on the boresight",
			helpURL = helpURL,
		)
		
		self.manGuideBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Man Guide",
			callFunc = self.doManGuide,
			helpText = "Expose repeatedly; center with ctrl-click or Nudger",
			helpURL = helpURL,
		)
		
		self.guideOnBoresightBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Guide on Slit",
			callFunc = self.doGuideOnBoresight,
			helpText = "Guide on object in slit",
			helpURL = helpURL,
		)

		if self.guideModel.gcamInfo.slitViewer:
			guideText = "Guide on Field Star"
			guideHelpText = "Guide on selected field star"
		else:
			guideText = "Guide"
			guideHelpText = "Guide on selected star"
		self.guideOnBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = guideText,
			callFunc = self.doGuideOn,
			helpText = guideHelpText,
			helpURL = helpURL,
		)
		
		self.guideOffBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Stop Guiding",
			callFunc = self.doGuideOff,
			helpText = "Turn off guiding",
			helpURL = helpURL,
		)
		
		self.cancelBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Cancel",
			callFunc = self.cmdCancel,
			helpText = "Cancel executing command",
			helpURL = helpURL,
		)
		
		self.ds9Btn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "DS9",
			callFunc = self.doDS9,
			helpText = "Display image in ds9",
			helpURL = helpURL,
		)
		
		# lay out command buttons
		if self.guideModel.gcamInfo.slitViewer:
			topRow = Tkinter.Frame(cmdButtonFrame)
			topRow.pack(side="top", expand=True, fill="x")
			topRow.lower()
			botRow = Tkinter.Frame(cmdButtonFrame)
			botRow.pack(side="top", expand=True, fill="x")
			botRow.lower()
	
			self.manGuideBtn.pack(side="left", in_ = topRow)
			self.guideOnBtn.pack(side="left", in_ = topRow)
	
			self.exposeBtn.pack(side="left", in_ = botRow)
			self.guideOnBoresightBtn.pack(side="left", in_=botRow)
			self.guideOffBtn.pack(side="left", in_=botRow)
			self.cancelBtn.pack(side="left", in_=botRow)
			# leave room for the resize control
			Tkinter.Label(botRow, text=" ").pack(side="right")
			self.ds9Btn.pack(side="right", in_=botRow)
			
		else:
			self.exposeBtn.pack(side="left")
			self.guideOnBtn.pack(side="left")
			self.guideOffBtn.pack(side="left")
			self.cancelBtn.pack(side="left")
			# leave room for the resize control
			Tkinter.Label(cmdButtonFrame, text=" ").pack(side="right")
			self.ds9Btn.pack(side="right")
			
			# enable controls accordingly
			self.enableCmdButtons()
			self.enableHistButtons()

		cmdButtonFrame.grid(row=row, column=0, sticky="ew")
		row += 1
		
		# event bindings
		self.gim.bind("<Map>", self.doMap)

		self.gim.cnv.bind("<Button-1>", self.doDragStart, add=True)
		self.gim.cnv.bind("<B1-Motion>", self.doDragContinue, add=True)
		self.gim.cnv.bind("<ButtonRelease-1>", self.doDragEnd, add=True)
		self.gim.cnv.bind("<Control-Button-1>", self.doCenterOnClick)
		
		self.threshWdg.bind("<FocusOut>", self.doFindStars)
		self.threshWdg.bind("<Return>", self.doFindStars)
		self.radMultWdg.bind("<FocusOut>", self.doFindStars)
		self.radMultWdg.bind("<Return>", self.doFindStars)
		
		# keyword variable bindings
		self.guideModel.fsActRadMult.addIndexedCallback(self.updRadMult)
		self.guideModel.fsActThresh.addIndexedCallback(self.updThresh)
		self.guideModel.files.addCallback(self.updFiles)
		self.guideModel.star.addCallback(self.updStar)
		self.guideModel.guideState.addCallback(self.updGuideState)

		# bindings to set the image cursor
		tl = self.winfo_toplevel()
		tl.bind("<Control-KeyPress>", self.cursorCtr, add=True)
		tl.bind("<Control-KeyRelease>", self.ignoreEvt, add=True)
		tl.bind("<KeyRelease>", self.cursorNormal, add=True)
		
		# exit handler
		atexit.register(self._exitHandler)
		
		self.enableCmdButtons()
		self.enableHistButtons()

	def _trackMem(self, obj, objName):
		"""Print a message when an object is deleted.
		"""
		if not _DebugMem:
			return
		objID = id(obj)
		def refGone(ref=None, objID=objID, objName=objName):
			print "GuideWdg deleting %s" % (objName,)
			del(self._memDebugDict[objID])

		self._memDebugDict[objID] = weakref.ref(obj, refGone)
		del(obj)

	def addImToHist(self, imObj, ind=None):
		imageName = imObj.imageName
		if ind == None:
			self.imObjDict[imageName] = imObj
		else:
			self.imObjDict.insert(ind, imageName, imObj)
	
	def cmdCancel(self, wdg=None):
		"""Cancel the current command.
		"""
		if self.doingCmd == None:
			return
		cmdVar = self.doingCmd[0]
		cmdVar.abort()

	def cmdCallback(self, msgType, msgDict, cmdVar):
		"""Use this callback when launching a command
		whose completion requires buttons to be re-enabled.
		
		DO NOT use it for very-long-duration commands, i.e. starting guiding.
		"""
		if self.doingCmd == None:
			return
		if self.doingCmd[0] == cmdVar:
			cmdBtn = self.doingCmd[1]
			if cmdBtn != None:
				cmdBtn.setEnable(True)
			self.doingCmd = None
		else:
			sys.stderr.write("GuideWdg warning: cmdCallback called for wrong cmd:\n- doing cmd: %s\n- called by cmd: %s\n" % (self.doingCmd[0], cmdVar))
		self.enableCmdButtons()

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
			self.statusBar.setMsg("Ctrl-click requires an image", severity = RO.Constants.sevError)
			self.statusBar.playCmdFailed()
			return
	
		if not self.guideModel.gcamInfo.slitViewer:
			self.statusBar.setMsg("Ctrl-click requires a slit viewer", severity = RO.Constants.sevError)
			self.statusBar.playCmdFailed()
			return
	
		if self.gim.mode != "normal": # recode to use a class constant
			self.statusBar.setMsg("Ctrl-click requires default mode (+ icon)", severity = RO.Constants.sevError)
			self.statusBar.playCmdFailed()
			return
		
		cnvPos = self.gim.cnvPosFromEvt(evt)
		imPos = self.gim.imPosFromCnvPos(cnvPos)
		
		cmdStr = "guide on imgFile=%r centerOn=%.2f,%.2f noGuide %s" % \
			(self.dispImObj.imageName, imPos[0], imPos[1], self.getExpArgStr(inclThresh=False))
		self.doCmd(cmdStr)
	
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
			(self.dispImObj.imageName, pos[0], pos[1], self.getExpArgStr(inclThresh=False)
		)
		self.doCmd(cmdStr)
	
	def doChooseIm(self, wdg):
		"""Choose an image to display.
		"""
		self.showCurrWdg.setBool(False)

		if self.dispImObj != None:
			currPath = self.dispImObj.getLocalPath()
			startDir, startFile = os.path.split(currPath)
		else:
			# use user preference for image directory, if available
			startDir = self.tuiModel.prefs.getValue("Save To")
			startFile = None
		newPath = tkFileDialog.askopenfilename(
			initialdir = startDir,
			initialfile = startFile,
			filetypes = (("FITS", "*.fits"), ("FITS", "*.fit"),),
		)
		if not newPath:
			return
		
		# try to find image in history
		# using samefile is safer than trying to match paths as strings
		# (RO.OS.expandPath *might* be thorough enough to allow that,
		# but no promises and one would have to expand every path being checked)
		for imObj in self.imObjDict.itervalues():
			try:
				isSame = os.path.samefile(newPath, imObj.getLocalPath())
			except OSError:
				continue
			if isSame:
				self.showImage(imObj)
				return
		# not in history; create new local imObj and load that

		# try to split off user's base dir if possible
		baseDir = ""
		imageName = newPath
		startDir = self.tuiModel.prefs.getValue("Save To")
		if startDir != None:
			startDir = RO.OS.expandPath(startDir)
			if startDir and not startDir.endswith(os.sep):
				startDir = startDir + os.sep
			newPath = RO.OS.expandPath(newPath)
			if newPath.startswith(startDir):
				baseDir = startDir
				imageName = newPath[len(startDir):]
		
		imObj = ImObj(
			baseDir = baseDir,
			imageName = imageName,
			cmdChar = "f",
			cmdr = self.tuiModel.getCmdr(),
			cmdID = 0,
			guideModel = self.guideModel,
			isLocal = True,
		)
		self._trackMem(imObj, str(imObj))
		imObj.fetchFile()
		ind = None
		if self.dispImObj != None:
			try:
				ind = self.imObjDict.index(self.dispImObj.imageName)
			except KeyError:
				pass
		self.addImToHist(imObj, ind)
		self.showImage(imObj)
		
	def doCmd(self,
		cmdStr,
		cmdBtn = None,
		isGuideOn = False,
		actor = None,
		abortCmdStr = None,
		cmdSummary = None,
	):
		"""Execute a command.
		Inputs:
		- cmdStr		the command to execute
		- cmdBtn		the button that triggered the command
		- isGuideOn		set True for commands that start guiding
		- actor			the actor to which to send the command;
						defaults to the actor for the guide camera
		- abortCmdStr	abort command, if any
		- cmdSummary	command summary for the status bar
		"""
		actor = actor or self.actor
		cmdVar = RO.KeyVariable.CmdVar(
			actor = actor,
			cmdStr = cmdStr,
			abortCmdStr = abortCmdStr,
		)
		if cmdBtn:
			self.doingCmd = (cmdVar, cmdBtn, isGuideOn)
			cmdVar.addCallback(
				self.cmdCallback,
				callTypes = RO.KeyVariable.DoneTypes,
			)
		else:
			self.doingCmd = None
		self.enableCmdButtons()
		self.statusBar.doCmd(cmdVar, cmdSummary)
	
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
	
	def doDragStart(self, evt):
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
	
	def doDragContinue(self, evt):
		if self.inCtrlClick:
			return
		if not self.gim.isNormalMode():
			return
		newPos = self.gim.cnvPosFromEvt(evt)
		self.gim.cnv.coords(self.dragRect, self.dragStart[0], self.dragStart[1], newPos[0], newPos[1])
	
	def doDragEnd(self, evt):
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
		thresh = self.threshWdg.getNum()
		
		if abs(deltaPos[0]) > 1 and abs(deltaPos[1] > 1):
			# centroid

			# execute centroid command
			cmdStr = "centroid file=%r on=%s,%s cradius=%s thresh=%s" % (self.dispImObj.imageName, imPos[0], imPos[1], rad, thresh)
			self.doCmd(cmdStr)
			if _LocalMode:
				GuideTest.centroid(self.dispImObj.imageName, on=imPos, rad=rad, thresh=thresh)
			
		else:
			# select
			self.doSelect(evt)

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
		cmdStr = "findstars " + self.getExpArgStr(inclRadMult=True)
		self.doCmd(cmdStr, cmdBtn=self.exposeBtn, cmdSummary="expose")
		
	def doFindStars(self, *args):
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return

		radMult = self.radMultWdg.getNum()
		if radMult == None:
			return
		thresh = self.threshWdg.getNum()
		if thresh == None:
			return
		if (radMult == self.dispImObj.currRadMult)\
			and (thresh == self.dispImObj.currThresh):
				return
		
		# not strictly necessary since the hub will return this data;
		# still, it is safer to set it now and be sure it gets set
		self.dispImObj.currThresh = thresh
		self.dispImObj.currRadMult = radMult
		
		# execute new command
		cmdStr = "findstars file=%r thresh=%s radMult=%s" % (self.dispImObj.imageName, thresh, radMult)
		self.doCmd(cmdStr)
		if _LocalMode:
			GuideTest.findStars(self.dispImObj.imageName, thresh=thresh, radMult=radMult)
	
	def doGuideOff(self, wdg=None):
		"""Turn off guiding.
		"""
		self.doCmd("guide off", cmdBtn=self.guideOffBtn)
	
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
		self.doCmd(cmdStr, cmdBtn = self.guideOnBtn, abortCmdStr="guide off", isGuideOn=True)
	
	def doGuideOnBoresight(self, wdg=None):
		"""Guide on boresight.
		"""
		cmdStr = "guide on boresight %s" % (self.getExpArgStr())
		self.doCmd(cmdStr, cmdBtn = self.guideOnBoresightBtn, abortCmdStr="guide off", isGuideOn=True)
	
	def doManGuide(self, wdg=None):
		"""Repeatedly expose. Let the user control-click to center up.
		"""
		self.doCmd(
			"guide on manual %s" % self.getExpArgStr(),
			cmdBtn = self.manGuideBtn,
			isGuideOn = True,
		)
	
	def doMap(self, evt=None):
		"""Window has been mapped"""
		if self.dispImObj:
			# give the guide frame a chance to be redrawn so zoom can be set correctly
			self.update_idletasks()
			self.showImage(self.dispImObj)
	
	def doNextIm(self, wdg=None):
		"""Show next image from history list"""
		revHist, currInd = self.getHistInfo()
		if currInd == None:
			self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevWarning)
			return

		try:
			nextImName = revHist[currInd-1]
		except IndexError:
			self.statusBar.setMsg("Showing newest image", severity = RO.Constants.sevWarning)
			return
		
		self.showImage(self.imObjDict[nextImName])
	
	def doPrevIm(self, wdg=None):
		"""Show previous image from history list"""
		self.showCurrWdg.setBool(False)

		revHist, currInd = self.getHistInfo()
		if currInd == None:
			self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevError)
			return

		try:
			prevImName = revHist[currInd+1]
		except IndexError:
			self.statusBar.setMsg("Showing oldest image", severity = RO.Constants.sevWarning)
			return
		
		self.showImage(self.imObjDict[prevImName])
			
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
		"""Handle show current image button"""
		doShowCurr = self.showCurrWdg.getBool()
		
		if doShowCurr:
			sev = RO.Constants.sevNormal
			helpText = "Show new images; click to hold this image"
		else:
			sev = RO.Constants.sevWarning
			helpText = "Hold this image; click to show new images"
		self.showCurrWdg.setSeverity(sev)
		self.showCurrWdg.helpText = helpText
		
		if not doShowCurr:
			return

		# show most recent downloaded image, if any, else most recent image
		revHist = self.imObjDict.values()
		if not revHist:
			return

		for imObj in revHist:
			if imObj.isDone():
				break
		else:
			# display show most recent image
			imObj = revHist[0]
		
		self.showImage(imObj, forceCurr=True)
	
	def doShowHideImage(self, wdg=None):
		"""Handle show/hide image button
		"""
		doShow = self.showHideImageWdg.getBool()
		if doShow:
			self.gim.grid()
		else:
			self.gim.grid_remove()
	
	def enableCmdButtons(self):
		"""Set enable of command buttons.
		"""
		isImage = (self.dispImObj != None)
		isCurrIm = isImage and not self.nextImWdg.getEnable()
		isSel = (self.dispImObj != None) and (self.dispImObj.selDataColor != None)
		isGuiding = self.isGuiding()
		isExec = (self.doingCmd != None)
		isExecOrGuiding = isExec or isGuiding
		
		# set enable for buttons that can change; all others are always enabled
		self.exposeBtn.setEnable(not isExecOrGuiding)
		self.centerBtn.setEnable(isCurrIm and isSel and not isExecOrGuiding)
		self.guideOnBtn.setEnable(isCurrIm and isSel and not isExecOrGuiding)
		self.guideOnBoresightBtn.setEnable(not isExecOrGuiding)
		self.manGuideBtn.setEnable(not isExecOrGuiding)

		guideState, guideStateCurr = self.guideModel.guideState.getInd(0)
		gsLower = guideState and guideState.lower()
		self.guideOffBtn.setEnable(gsLower in ("on", "starting"))

		self.cancelBtn.setEnable(isExec)
		self.ds9Btn.setEnable(isImage)
		if (self.doingCmd != None) and (self.doingCmd[1] != None):
			self.doingCmd[1].setEnable(False)
	
	def enableHistButtons(self):
		"""Set enable of prev and next buttons"""
		revHist, currInd = self.getHistInfo()
		#print "currInd=%s, len(revHist)=%s, revHist=%s" % (currInd, len(revHist), revHist)
		enablePrev = enableNext = False
		prevGap = nextGap = False
		if (len(revHist) > 0) and (currInd != None):
			prevInd = currInd + 1
			if prevInd < len(revHist):
				enablePrev = True
				if not self.dispImObj.isInSequence:
					prevGap = True
				elif not (self.imObjDict[revHist[prevInd]]).isInSequence:
					prevGap = True
					
			nextInd = currInd - 1
			if not self.showCurrWdg.getBool() and nextInd >= 0:
				enableNext = True
				if not self.dispImObj.isInSequence:
					nextGap = True
				elif not (self.imObjDict[revHist[nextInd]]).isInSequence:
					nextGap = True
		
		self.prevImWdg.setState(enablePrev, prevGap)
		self.nextImWdg.setState(enableNext, nextGap)
				
	def fetchCallback(self, imObj):
		"""Called when an image is finished downloading.
		"""
		if self.showCurrWdg.getBool() or (self.dispImObj == imObj):
			self.showImage(imObj)
	
	def getExpArgStr(self, inclThresh = True, inclRadMult = False):
		"""Return exposure time, bin factor, thresh and radMult
		as a string suitable for a guide camera command.
		
		The defaults are suitable for autoguiding.
		Set inclRadMult true for finding stars.
		Set inclRadMult false for manual guiding.
		"""
		argList = []
		expTimeStr = self.expTimeWdg.getString()
		if expTimeStr:
			argList.append("exptime=" + expTimeStr)

		binFacStr = self.binFacWdg.getString()
		if binFacStr:
			argList.append("bin=" + binFacStr)

		if inclRadMult:
			radMultStr = self.radMultWdg.getString()
			if radMultStr:
				argList.append("radMult=" + radMultStr)
		
		if inclThresh:
			threshStr = self.threshWdg.getString()
			if threshStr:
				argList.append("thresh=" + threshStr)
		
		return " ".join(argList)
	
	def getHistInfo(self):
		"""Return information about the location of the current image in history.
		Returns:
		- revHist: list of image names in history in reverse order (most recent first)
		- currImInd: index of displayed image in history
		  or None if no image is displayed or displayed image not in history at all
		"""
		revHist = self.imObjDict.keys()
		if self.dispImObj == None:
			currImInd = None
		else:
			try:
				currImInd = revHist.index(self.dispImObj.imageName)
			except ValueError:
				currImInd = None
		return (revHist, currImInd)
	
	def ignoreEvt(self, evt=None):
		pass

	def imObjFromKeyVar(self, keyVar):
		"""Return imObj that matches keyVar's cmdr and cmdID, or None if none"""
		cmdrCmdID = keyVar.getCmdrCmdID()
		if cmdrCmdID == None:
			return None
		for imObj in self.imObjDict.itervalues():
			if cmdrCmdID == imObj.currCmdrCmdID:
				return imObj
		return None
	
	def isDispObj(self, imObj):
		"""Return True if imObj is being displayed, else False"""
		return self.dispImObj and (self.dispImObj.imageName == imObj.imageName)
	
	def isGuiding(self):
		"""Return True if guiding"""
		guideState, guideStateCurr = self.guideModel.guideState.getInd(0)
		if guideState == None:
			return False

		return guideState.lower() != "off"

	def showImage(self, imObj, forceCurr=None):
		"""Display an image.
		Inputs:
		- imObj	image to display
		- forceCurr	force guide params to be set to current value?
			if None then automatically set based on the Current button
		"""
		#print "showImage(imObj=%s)" % (imObj,)
		# expire current image if not in history (this should never happen)
		if (self.dispImObj != None) and (self.dispImObj.imageName not in self.imObjDict):
			sys.stderr.write("GuideWdg warning: expiring display image that was not in history")
			self.dispImObj.expire()
		
		fitsIm = imObj.getFITSObj()
		#print "fitsIm=%s, self.gim.ismapped=%s" % (fitsIm, self.gim.winfo_ismapped())
		if fitsIm:
			#self.statusBar.setMsg("", RO.Constants.sevNormal)
			imArr = fitsIm[0].data
			imHdr = fitsIm[0].header
			expTime = imHdr.get("EXPTIME")
			binFac = imHdr.get("BINX")
		else:
			if imObj.didFail():
				sev = RO.Constants.sevNormal
			else:
				if (imObj.state == imObj.StReady) and self.gim.winfo_ismapped():
					# image not downloaded earlier because guide window was hidden at the time
					# get it now
					imObj.fetchFile()
				sev = RO.Constants.sevNormal
			self.gim.showMsg(imObj.getStateStr(), sev)
			imArr = None
			expTime = None
			binFac = None
	
		# display new data
		self.gim.showArr(imArr)
		self.dispImObj = imObj
		self.imNameWdg.set(imObj.imageName)
		self.imNameWdg.xview("end")
		
		# update guide params
		# if looking through the history then force current values to change
		# otherwise leave them alone unless they are already tracking the defaults
		if forceCurr == None:
			forceCurr = not self.showCurrWdg.getBool()

		if forceCurr or self.expTimeWdg.getIsCurrent():
			self.expTimeWdg.set(expTime)
		self.expTimeWdg.setDefault(expTime)

		if forceCurr or self.binFacWdg.getIsCurrent():
			self.binFacWdg.set(binFac)
		self.binFacWdg.setDefault(binFac)
		
		if forceCurr or self.threshWdg.getIsCurrent():
			if imObj.currThresh != None:
				self.threshWdg.set(imObj.currThresh)
			else:
				self.threshWdg.set(imObj.defThresh)
		self.threshWdg.setDefault(imObj.defThresh)

		if forceCurr or self.radMultWdg.getIsCurrent():
			if imObj.currRadMult != None:
				self.radMultWdg.set(imObj.currRadMult)
			else:
				self.radMultWdg.set(imObj.defRadMult)
		self.radMultWdg.setDefault(imObj.defRadMult)	
		
		self.enableHistButtons()
		
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
			# disable command buttons accordingly
			self.enableCmdButtons()
			
			# clear data display
			self.starXPosWdg.set(None)
			self.starYPosWdg.set(None)
			self.starFWHMWdg.set(None)
			self.starAmplWdg.set(None)
			self.starBkgndWdg.set(None)
			return
		
		starData, color = self.dispImObj.selDataColor

		# draw selection
		self.gim.addAnnotation(
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
	
		# enable command buttons accordingly
		self.enableCmdButtons()
		
	def updFiles(self, fileData, isCurrent, keyVar):
		"""Handle files keyword
		"""
		#print "%s updFiles(fileData=%r; isCurrent=%r)" % (self.actor, fileData, isCurrent)
		if not isCurrent:
			return
		
		cmdChar, isNew, baseDir, imageName, maskName = fileData[0:5]
		cmdr, cmdID = keyVar.getCmdrCmdID()
		imageName = baseDir + imageName
		if maskName:
			maskName = baseDir + maskName

		if not isNew:
			# handle data for existing image
			self.doExistingImage(imageName, cmdChar, cmdr, cmdID)
			return
		
		# at this point we know we have a new image
		
		# create new object data
		baseDir = self.guideModel.ftpSaveToPref.getValue()
		defRadMult = self.guideModel.fsDefRadMult.getInd(0)[0]
		defThresh = self.guideModel.fsDefThresh.getInd(0)[0]
		imObj = ImObj(
			baseDir = baseDir,
			imageName = imageName,
			cmdChar = cmdChar,
			cmdr = cmdr,
			cmdID = cmdID,
			guideModel = self.guideModel,
			fetchCallFunc = self.fetchCallback,
			defRadMult = defRadMult,
			defThresh = defThresh,
		)
		self._trackMem(imObj, str(imObj))
		self.addImToHist(imObj)
		
		if self.gim.winfo_ismapped():
			imObj.fetchFile()
			if (self.dispImObj == None or self.dispImObj.didFail()) and self.showCurrWdg.getBool():
				self.showImage(imObj)
		elif self.showCurrWdg.getBool():
			self.showImage(imObj)

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
# once you know what to do with mask files, start fetching them
# but some callback should be listening for them
# and there should be some easy way to display them
#				maskObj.fetchFile()
			imObj.maskObj = maskObj

		# purge excess images
		if self.dispImObj:
			dispImName = self.dispImObj.imageName
		else:
			dispImName = ()
		isNewest = True
		if len(self.imObjDict) > self.nToSave:
			keys = self.imObjDict.keys()
			for imName in keys[self.nToSave:]:
				if imName == dispImName:
					if not isNewest:
						self.imObjDict[imName].isInSequence = False
					continue
				if _DebugMem:
					print "Purging %r from history" % (imName,)
				purgeImObj = self.imObjDict.pop(imName)
				purgeImObj.expire()
				isNewest = False
		self.enableHistButtons()

	def updGuideState(self, guideState, isCurrent, keyVar):
		if not isCurrent:
			return
		
		# first handle disable of guide on buttons when guiding starts
		if self.doingCmd and self.doingCmd[2]:
			gsLower = guideState[0] and guideState[0].lower()
			if gsLower != "off":
				cmdVar = self.doingCmd[0]
				self.doingCmd = None
		guideState = [item for item in guideState if item]
		stateStr = "-".join(guideState)
		self.guideStateWdg.set(stateStr, severity = keyVar.getSeverity())
		self.enableCmdButtons()
	
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
		imObj = self.imObjFromKeyVar(keyVar)
		if not imObj:
			return
		
		isVisible = self.isDispObj(imObj)
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
	
	def updRadMult(self, radMult, isCurrent, keyVar):
		"""New radMult data found.
		"""
		#print "%s updRadMult(radMult=%r, isCurrent=%r)" % (self.actor, radMult, isCurrent)
		if not isCurrent:
			return

		imObj = self.imObjFromKeyVar(keyVar)
		if imObj == None:
			return
		
		if imObj.currRadMult == None:
			imObj.defRadMult = radMult
		imObj.currRadMult = radMult

		if self.isDispObj(imObj):
			if self.radMultWdg.getIsCurrent():
				self.radMultWdg.set(imObj.currRadMult)
			self.radMultWdg.setDefault(imObj.defRadMult)

	def updThresh(self, thresh, isCurrent, keyVar):
		"""New threshold data found.
		"""
		if not isCurrent:
			return

		imObj = self.imObjFromKeyVar(keyVar)
		if imObj == None:
			return
		
		if imObj.currThresh == None:
			imObj.defThresh = thresh
		imObj.currThresh = thresh

		if self.isDispObj(imObj):
			if self.threshWdg.getIsCurrent():
				self.threshWdg.set(imObj.currThresh)
			self.threshWdg.setDefault(imObj.defThresh)
		
	def _exitHandler(self):
		"""Delete all image files and mask files.
		"""
		for maskObj in self.maskDict.itervalues():
			maskObj.expire()
		for imObj in self.imObjDict.itervalues():
			imObj.expire()
		

if __name__ == "__main__":
	import GuideTest
	#import gc
	#gc.set_debug(gc.DEBUG_SAVEALL) # or gc.DEBUG_LEAK to print lots of messages
	
	isLocal = True  # run local tests?
	_LocalMode = isLocal # not needed for other modules

	root = RO.Wdg.PythonTk()

	GuideTest.init("ecam", isLocal = isLocal)

	testFrame = GuideWdg(root, "ecam")
	testFrame.pack(expand="yes", fill="both")
	testFrame.wait_visibility() # must be visible to download images

	if isLocal:
		GuideTest.runLocalDemo()
#		GuideTest.runLocalFiles(2)
	else:
		GuideTest.runDownload(
			basePath = "keep/gcam/UT050422/",
			startNum = 101,
			numImages = 20,
			maskNum = 1,
			waitMs = 2500,
		)

	root.mainloop()