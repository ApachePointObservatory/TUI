#!/usr/local/bin/python
"""GuideImage represents a guide image

History:
2006-08-03 ROwen	Separated ImObj out of GuideWdg.py into this file
					and renamed to GuideImage.
"""
import os
import pyfits
import TUI.HubModel

_DebugMem = False # print a message when a file is deleted from disk?

class BasicImage(object):
	"""Information about an image.
	
	Inputs:
	- localBaseDir	root image directory on local machine
	- imageName	path to image relative, specifically:
				if isLocal False, then a URL relative to the download host
				if isLocal True, then a local path relative to localBaseDir
	- imageName	unix path to image, relative to host root directory
	- guideModel	guide model for this actor
	- fetchCallFunc	function to call when image info changes state
	- isLocal	set True if image is local or already downloaded
	"""
	Ready = "Ready to download"
	Downloading = "Downloading"
	Downloaded = "Downloaded"
	FileReadFailed = "Cannot read file"
	DownloadFailed = "Download failed"
	Expired = "Expired; file deleted"
	ErrorStates = (FileReadFailed, DownloadFailed, Expired)
	DoneStates = (Downloaded,) + ErrorStates

	def __init__(self,
		localBaseDir,
		imageName,
		downloadWdg = None,
		fetchCallFunc = None,
		isLocal = False,
	):
		#print "%s localBaseDir=%r, imageName=%s" % (self.__class__.__name__, localBaseDir, imageName)
		self.localBaseDir = localBaseDir
		self.imageName = imageName
		self.downloadWdg = downloadWdg
		self.hubModel = TUI.HubModel.getModel()
		self.errMsg = None
		self.fetchCallFunc = fetchCallFunc
		self.isLocal = isLocal
		if not self.isLocal:
			self.state = self.Ready
		else:
			self.state = self.Downloaded
		self.isInSequence = not isLocal
		
		# set local path
		# this split suffices to separate the components because image names are simple
		if isLocal:
			self.localPath = os.path.join(self.localBaseDir, imageName)
		else:
			pathComponents = self.imageName.split("/")
			self.localPath = os.path.join(self.localBaseDir, *pathComponents)
		#print "GuideImage localPath=%r" % (self.localPath,)
	
	def didFail(self):
		"""Return False if download failed or image expired"""
		return self.state in self.ErrorStates
	
	def expire(self):
		"""Delete the file from disk and set state to expired.
		"""
		if self.isLocal:
			if _DebugMem:
				print "Would delete %r, but is local" % (self.imageName,)
			return
		if self.state == self.Downloaded:
			# don't use _setState because no callback wanted
			# and _setState ignored new states once done
			self.state = self.Expired
			if os.path.exists(self.localPath):
				if _DebugMem:
					print "Deleting %r" % (self.localPath,)
				os.remove(self.localPath)
			elif _DebugMem:
				print "Would delete %r, but not found on disk" % (self.imageName,)
		elif _DebugMem:
			print "Would delete %r, but state = %r is not 'downloaded'" % (self.imageName, self.state,)

	def fetchFile(self):
		"""Start downloading the file."""
		#print "%s fetchFile; isLocal=%s" % (self, self.isLocal)
		if self.isLocal:
			self._setState(self.Downloaded)
			return

		host, hostRootDir = self.hubModel.httpRoot.get()[0]
		if None in (host, hostRootDir):
			self._setState(
				self.DownloadFailed,
				"Cannot download images; hub httpRoot keyword not available",
			)
			return

		self._setState(self.Downloading)

		fromURL = "".join(("http://", host, hostRootDir, self.imageName))
		self.downloadWdg.getFile(
			fromURL = fromURL,
			toPath = self.localPath,
			isBinary = True,
			overwrite = True,
			createDir = True,
			doneFunc = self._fetchDoneFunc,
			dispStr = self.imageName,
		)
		
	def getFITSObj(self):
		"""If the file is available, return a pyfits object,
		else return None.
		"""
		if self.state == self.Downloaded:
			try:
				fitsIm = pyfits.open(self.getLocalPath())
				if fitsIm:
					return fitsIm
				
				self.state = self.FileReadFailed
				self.errMsg = "No image data found"
				return None
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				self.state = self.FileReadFailed
				self.errMsg = str(e)
		return None
	
	def getLocalPath(self):
		"""Return the full local path to the image."""
		return self.localPath
	
	def getStateStr(self):
		"""Return a string describing the current state."""
		if self.errMsg:
			return "%s: %s" % (self.state, self.errMsg)
		return self.state

	def isDone(self):
		"""Return True if download finished (successfully or otherwise)"""
		return self.state in self.DoneStates

	def _fetchDoneFunc(self, httpGet):
		"""Called when image download ends.
		"""
		if httpGet.getState() == httpGet.Done:
			self._setState(self.Downloaded)
		else:
			self._setState(self.DownloadFailed, httpGet.getErrMsg())
			#print "%s download failed: %s" % (self, self.errMsg)
	
	def _setState(self, state, errMsg=None):
		if self.isDone():
			return
	
		self.state = state
		if self.didFail():
			self.errMsg = errMsg
		
		if self.fetchCallFunc:
			self.fetchCallFunc(self)
		if self.isDone():
			self.fetchCallFunc = None
	
	def __str__(self):
		return "%s(%s)" % (self.__class__.__name__, self.imageName)


class GuideImage(BasicImage):
	def __init__(self,
		localBaseDir,
		imageName,
		downloadWdg = None,
		fetchCallFunc = None,
		defRadMult = None,
		defThresh = None,
		defGuideMode = None,
		isLocal = False,
	):
		self.starDataDict = {} # dict of star type char: star keyword data
		self.defSelDataColor = None
		self.selDataColor = None
		self.guiderPredPos = None
		self.defRadMult = defRadMult
		self.defThresh = defThresh
		self.defGuideMode = defGuideMode
		self.currRadMult = None
		self.currThresh = None
		self.currGuideMode = None

		BasicImage.__init__(self,
			localBaseDir = localBaseDir,
			imageName = imageName,
			downloadWdg = downloadWdg,
			fetchCallFunc = fetchCallFunc,
			isLocal = isLocal,
		)


