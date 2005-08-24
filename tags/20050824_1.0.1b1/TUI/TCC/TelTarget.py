#!/usr/local/bin/python
"""
History:
2003-10-21 ROwen	Renamed SetInfo to setInfo (standard case convention);
					modified setInfo to use Date as a separate argument,
					to match new value dictionary.
2003-10-29 ROwen	Added the ability to set info at object creation;
					modified to be set from a value dictionary;
					moved from TUI to TUI.TCC.
2004-03-04 ROwen	TelTarget class:
					- Made ObsData and TopoConst class instances, since they are constants.
					- Renamed.setInfo to setValueDict.
					Added Catalog class.
2004-08-10 ROwen	Modified to use RO.Wdg.colorOK.
2005-06-08 ROwen	Changed TelTarget to a new-style class.
2005-07-07 ROwen	Modified for moved RO.TkUtil.
"""
import sys
import time
import RO.AddCallback
import RO.SeqUtil
import RO.StringUtil
import RO.Astro.Cnv
import RO.Astro.Sph
import RO.CoordSys
import RO.MathUtil
import RO.TkUtil
import TelConst

# default color for displaying catalog objects
_DefColor = 'black'

class TelTarget(object):
	"""A potential target position for the telescope.
	It is primarily used to display that position on an az/alt display.
	
	WARNING: when doing coordinate conversions, treat Observed and Physical
	as Topocentric (since we have no knowledge of refraction coefficients yet)
	and treat Mount without any attempt to wrap.
	"""
	ObsData = RO.Astro.Cnv.ObserverData(
		TelConst.Longitude, TelConst.Latitude, TelConst.Elevation,
	)
	TopoConst = RO.CoordSys.getSysConst(RO.CoordSys.Topocentric)

	def __init__(self, valueDict=None):
		self.setValueDict(valueDict)

	def getAzAlt(self):
		"""Returns the current (az, alt) of the object, in degrees"""
		if self.csysConst == None:
			return None
			
		toPos, toPM, toParlax, toRadVel, toDir, scaleChange, atInf, atPole = RO.Astro.Sph.coordConv(
			fromPos = self.posDeg,
			fromSys = self.csysConst.name(),
			fromDate = self.dateFloat,
			toSys = self.TopoConst.name(),
			toDate = None,
			obsData = self.ObsData,
			fromPM = self.pm,
			fromParlax = self.parlax,
			fromRadVel = self.radVel,
		)
		# eventually we'll want to handle toDir as well, but for now...
		return toPos
	
	def getValueDict(self):
		"""Return the value dictionary.
		"""
		return self.valueDict
	
	def setValueDict(self,
		valueDict = None,
	):
		"""Specify information about the object.
		All data must be strings!!!
		
		This information typically comes directly from a value dictionary
		generated by the SetObjPos widget, e.g. myObj.setValueDict(**valueDict).
		That's why the variable names are in uppercase.

		Inputs:
		- valueDict: the following keys are used; the rest are recorded and ignored
			- ObjPos	equatorial, polar angle of object position;
						equatorial is d'" or hms, depending on RO.CoordSys;
						polar is always d'"
			- CSys		coordinate system name
			- Date		date of observation and/or equinox;
						units of date and default value depends on coordinate system
			- Name		object name
			- PM		proper motion
			- Px		parallax
			- Rv		radial velocity
			- Distance	distance (1/parallax); overrides Px if supplied
			- DispColor	color with which to display on sky widget;
						any false value means "do not display"
		"""
		if valueDict == None:
			valueDict = {"ObjPos":("0", "0"), "CSys":"ICRS", "Date":"2000", "Name":""}
		self.valueDict = valueDict

		self.name = valueDict.get("Name")
		self.posStr = valueDict.get("ObjPos")
#		print "setValueDict(%r, %r, %r, %r, %r, %r, %r, %r)" % (ObjPos, CSys, Date, Name, PM, Px, Rv, Distance)
		
		Date = valueDict.get("Date")
		if Date not in (None, ""):
			self.dateFloat = float(Date)
			self.dateStr = Date
		else:
			self.dateFloat = None
			self.dateStr = ""
		
		# treat Observed, Mount and Physical as Topocentric
		CSys = valueDict.get("CSys")
		if CSys in (None, ""):
			self.approxCSys = None
			self.csysConst = None
			self.posDeg = None
			self.userP = None
			self.userV = None
			return
		self.csysStr = CSys

		if CSys in (RO.CoordSys.Observed, RO.CoordSys.Physical, RO.CoordSys.Mount):
			self.approxCSys = RO.CoordSys.Topocentric
		else:
			self.approxCSys = CSys
		
		self.csysConst = RO.CoordSys.getSysConst(self.approxCSys)
				
		# get position in degrees
		self.posDeg = self.csysConst.posDegFromDispStr(*self.posStr)
		
		PM = valueDict.get("PM", ("", ""))
		Px = valueDict.get("Px", "")
		Rv = valueDict.get("Rv", "")
		Distance = valueDict.get("Distance")

		# get proper motion, etc.
		self.pm = [RO.StringUtil.floatFromStr(pmstr) for pmstr in PM]
		self.parlax = 0.0
		if Distance != None:
			dist = RO.StringUtil.floatFromStr(Distance)
			if dist > 0.0:
				self.parlax = 1.0 / dist
		else:
			self.parlax = RO.StringUtil.floatFromStr(Px)
		self.radVel = RO.StringUtil.floatFromStr(Rv)
#		print "date, pm = ", self.dateFloat, self.pm
		
	def __str__(self):
		"""Return a string representation for this object.
		"""
		csysStr = self.csysStr
		if self.dateStr:
			csysStr = "=".join((csysStr, self.dateStr))
		return "%r %s, %s %s" % (self.name, self.posStr[0], self.posStr[1], csysStr)

class Catalog(RO.AddCallback.BaseMixin):
	"""A catalog of TelTarget objects.
	
	Inputs:
	- name		name of catalog
	- objList	a sequence of TelTarget objects
	- doDisplay	display the catalog objects on the sky display?
	- dispColor	color in which to display the items on the sky display;
				if None a default is used
	- callFunc	function to call when dispColor or doDisplay changed;
				receives one argument: this catalog
	"""

	_TestFrame = None

	def __init__(self,
		name,
		objList,
		doDisplay = True,
		dispColor = None,
		callFunc = None,
	):
		RO.AddCallback.BaseMixin.__init__(self)

		self.name = name
		if not RO.SeqUtil.isSequence(objList):
			raise RuntimeError("objList=%r; must be a sequence" % objList)
		self.objList = objList

		self.setDoDisplay(doDisplay)
		self.setDispColor(dispColor)
		
		if callFunc:
			self.addCallback(callFunc)
	
	def getDispColor(self):
		"""Returns the desired display color.
		"""
		return self._dispColor
	
	def getDoDisplay(self):
		"""Returns whether the catalog's objects should be displayed on a sky grid.
		"""
		return self._doDisplay
	
	def getObjList(self):
		"""Return the object list.

		This is not a copy, so don't mess with it.
		"""
		return self.objList

	def setDispColor(self, color=None):
		"""Set the color with which to display objects on a sky grid.
		If None, uses default color.
		
		Prints a warning to stderr and uses _DefColor if color invalid.
		"""
#		print "setDispColor(%r)" % (color,)
		if color == None:
			color = _DefColor
		else:
			if not RO.TkUtil.colorOK(color):
				sys.stderr.write("Invalid display color %r for %r; using %r\n" % (color, self, _DefColor))
				color = _DefColor
#		print "setDispColor setting color %r" % (color,)
		self._dispColor = color
		self._doCallbacks()

	def setDoDisplay(self, doDisplay):
		"""Set whether the catalog's objects should be displayed on a sky grid.
		"""
#		print "setDoDisplay(%r)" % (doDisplay,)
		self._doDisplay = bool(doDisplay)
		self._doCallbacks()
