#!/usr/local/bin/python
"""Retrieve a remote file via ftp to a local file.

The retrieval occurs in a background thread.

Note: I originally had abort in its own thread, but this sometimes failed
in a nasty way. It turns out to be unsafe to close a file in one thread
while it is being read in another thread.

Note: originally use urllib, but a nasty bug in urllib (Python 2.3 and 2.4b1)
prevented multiple transfers from working reliably.

History:
2003-09-25 ROwen
2003-10-06 ROwen	Changed background threads to daemonic, for fast exit
2003-10-16 ROwen	Bug fix: createDir mis-referenced (thanks, Craig Loomis).
2004-05-18 ROwen	Bug fix: used sys for reporting errors but did not import it.
2004-11-17 ROwen	Renamed from FTPGet and overhauled to use ftplib
					and consequently an entirely different interface.
2004-11-19 ROwen	Bug fix: was not setting TYPE I for binary.
"""
__all__ = ['FTPGet'] # state constants added below

import os
import sys
import urlparse
import threading
import ftplib
import RO.AddCallback

# state constants
# values <= 0 mean the transaction has finished
Queued = 4
Connecting = 3
Running = 2
Aborting = 1
Done = 0
Aborted = -1
Failed = -2

_StateDict = {
	Queued: "Queued",
	Connecting: "Connecting",
	Running: "Running",
	Aborting: "Aborting",
	Done: "Done",
	Aborted: "Aborted",
	Failed: "Failed",
}

__all__ += _StateDict.keys()

_Debug = False

StateStrMaxLen = 0
for _stateStr in _StateDict.itervalues():
	StateStrMaxLen = max(StateStrMaxLen, len(_stateStr))
del(_stateStr)

class FTPGet(RO.AddCallback.BaseMixin):
	"""Retrieves the specified url to a file.
	
	If the transfer is not started immediately then the following is done twice,
	first at object creation and again when the transfer is started:
	- if overwrite False, verify that the output file does not exist
	- if createDir True, create the output directory
			
	Inputs:
	- host	IP address of ftp host
	- fromPath	full path of file on host to retrieve
	- toPath	full path of destination file
	- isBinary	file is binary? (if False, EOL translation is probably performed)
	- overwrite: if True, overwrites the destination file if it exists;
		otherwise raises ValueError
	- createDir: if True, creates any required directories;
		otherwise raises ValueError
	- callFunc: called whenever more data is read or the state changes
		(except when the state changes to Aborting, due to thread issues);
		receives one argument: this object
	- startNow: if True, the transfer is started immediately
		otherwise callFunc is called and the transaction remains Queued
		until start is called
	- dispStr	a string to display while downloading the file;
				if omitted, an ftp URL (with no username/password) is created
	- username	the usual; *NOT SECURE*
	- password	the usual; *NOT SECURE*
	"""
	def __init__(self,
		host,
		fromPath,
		toPath,
		isBinary = True,
		overwrite = False,
		createDir = True,
		callFunc = None,
		startNow = True,
		dispStr = None,
		username = None,
		password = None,
	):
		self.host = host
		self.fromPath = fromPath
		self.toPath = toPath
		self.isBinary = isBinary
		self.overwrite = bool(overwrite)
		self.createDir = createDir
		self.username = username or "anonymous"
		self.password = password or "abc@def.org"
		
		if dispStr == None:
			self.dispStr = urlparse.urljoin("ftp://" + self.host, self.fromPath)
		else:
			self.dispStr = dispStr

		self._fromSocket = None
		self._toFile = None
		self._readBytes = 0
		self._totBytes = None
		self._state = Queued
		self._exception = None
		self._stateLock = threading.RLock()
		
		# set up background thread
		self._getThread = threading.Thread(name="get", target=self._getTask)
		self._getThread.setDaemon(True)
		
		# initialize parent classes		
		RO.AddCallback.BaseMixin.__init__(self, callFunc)		

		if startNow:
			self.start()
		else:
			self._toPrep()
			self._doCallbacks()
					
	def start(self):
		"""Start the download.
		
		If state is not Queued, raises RuntimeError
		"""
		self._stateLock.acquire()
		try:
			if self._state != Queued:
				raise RuntimeError, "state = %r not Queued" % self.getState()
			self._state = Connecting
		finally:
			self._stateLock.release()
		self._getThread.start()

	def abort(self):
		"""Start aborting: cancel the transaction and delete the output file.
		Silently fails if the transaction has already completed
		"""
		self._stateLock.acquire()
		try:
			if self._state == Queued:
				self._state = Aborted
				self._doCallbacks()
			elif self._state > 0:
				self._state = Aborting
			else:
				return
		finally:
			self._stateLock.release()	

	def getException(self):
		"""If the state is Failed, returns the exception that caused the failure.
		Otherwise returns None.
		"""
		return self._exception
	
	def getReadBytes(self):
		"""Returns bytes read so far
		"""
		return self._readBytes
	
	def getState(self):
		"""Returns the current state as an integer.
		"""
		return self._state
	
	def getStateStr(self, state=None):
		"""Returns the state as a descriptive string.
		
		Inputs:
		- state: state in question; if None then the current state is used.
		"""
		if state == None:
			state = self._state
		try:
			return _StateDict[state]
		except KeyError:
			return "Unknown (%r)" % (state)

	def getTotBytes(self):
		"""Return total bytes in file, if known, None otherwise.
		The value is certain to be unknown until the transfer starts;
		after that it depends on whether the server sends the info.
		"""
		return self._totBytes
	
	def isDone(self):
		"""Returns True if the transaction is finished
		(succeeded, aborted or failed), False otherwise.
		"""
		return self._state <= 0
	
	def _cleanup(self, newState, exception=None):
		"""Clean up everything. Must only be called from the _getTask thread.
		
		Close the input and output files.
		If not isDone() (transfer not finished) then updates the state
		and (after all other tasks) call the callbacks.
		If newState in (Aborted, Failed) and not isDone(), deletes the file
		If newState == Failed and not isDone(), sets the exception
		
		Inputs:
		- newState: new state; ignored if isDone()
		- exception: exception that is the reason for failure;
			ignored unless newState = Failed and not isDone()
		"""
		if _Debug:
			print "_cleanup(%r, %r=%s)" % (_StateDict[newState], exception, exception)
		if self._toFile:
			self._toFile.close()
		if _Debug:
			print "_toFile closed"
		if self._fromSocket:
			self._fromSocket.close()
		if _Debug:
			print "_fromSocket closed"

		# if state is not valid, warn and set to Failed
		if newState not in _StateDict:
			sys.stderr.write("FTPGet._cleanup unknown state %r; assuming %s=Failed\n" % (newState, Failed))
			newState = Failed
		
		self._stateLock.acquire()
		try:
			if self.isDone():
				# quit now if the transaction is finished
				return
			else:
				self._state = newState
		finally:
			self._stateLock.release()
		
		if newState in (Aborted, Failed):
			try:
				os.remove(self.toPath)
			except OSError:
				pass
			
			if newState == Failed:
				self._exception = exception
		self._doCallbacks()
	
	def __del__(self):
		"""It would be better to directly kill the connection,
		but I've not found any way to safely close the socket in one thread
		when it's being read in a different thread.
		"""
		self.abort()

	def _getTask(self):
		"""Retrieve the file in a background thread.
		Do not call directly; use start() instead.
		"""
		try:
			if _Debug:
				print "FTPGet: _getTask begins"

			# verify output file and verify/create output directory, as appropriate
			self._toPrep()

			# open output file
			if _Debug:
				print "FTPGet: opening output file %r" % (self.toPath,)
			if self.isBinary:
				mode = "wb"
			else:
				mode = "w"
			self._toFile = file(self.toPath, mode)

			# open input socket
			if _Debug:
				print "FTPGet: open ftp connection to %r" % (self.host)
			ftp = ftplib.FTP(self.host, self.username, self.password)
			
			if _Debug:
				print "FTPGet: set connection to binary=%r on %r" % (self.isBinary, self.host)
			if self.isBinary:
				ftp.voidcmd("TYPE I")
			else:
				ftp.voidcmd("TYPE A")

			if _Debug:
				print "FTPGet: open socket to %r on %r" % (self.fromPath, self.host)
			self._fromSocket, self._totBytes = ftp.ntransfercmd('RETR %s' % self.fromPath)

			
			self._state = Running
			if _Debug:
				print "FTPGet: totBytes = %r; read %r on %r " % \
					(self._totBytes, self.fromPath, self.host)
			
			while True:
				nextData = self._fromSocket.recv(8192)
				if not nextData:
					break
				elif self._state == Aborting:
					self._cleanup(Aborted)
					return
				self._readBytes += len(nextData)
				self._toFile.write(nextData)
				self._doCallbacks()
			
			self._cleanup(Done)
		except Exception, e:
			self._cleanup(Failed, exception = e)

	def _toPrep(self):
		"""Create or verify the existence of the output directory
		and check if output file already exists.
		
		Raises an exception if anything is wrong.
		"""
		# if output file exists and not overwrite, complain
		if not self.overwrite and os.path.exists(self.toPath):
			raise ValueError, "toPath %r already exists" % (self.toPath,)
		
		# if directory does not exist, create it or fail, depending on createDir;
		# else if "directory" exists but is a file, fail
		toDir = os.path.dirname(self.toPath)
		if toDir:
			if not os.path.exists(toDir):
				# create the directory or fail, depending on createDir
				if self.createDir:
					os.makedirs(toDir)
				else:
					raise ValueError, "directory %r does not exist" % (toDir,)
			elif not os.path.isdir(toDir):
				raise RuntimeError, "%r is a file, not a directory" % (toDir,)
