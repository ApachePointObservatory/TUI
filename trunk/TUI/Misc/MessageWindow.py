#!/usr/local/bin/python
"""Instant messaging widget.

History:
2003-03-28 ROwen
2003-04-01 ROwen	bug fix: infinite repeat of last msg when disconnected
2003-04-07 ROwen	connected the help and made the upper panel read-only;
					(somehow those lines had gotten commented out).
2003-05-08 ROwen	Modified to use RO.CnvUtil.
2003-06-09 ROwen	Removed some args from addWindow and MessageWdg.
2003-06-09 ROwen	Removed most args from StatusConfiWdg.__init__.
2003-06-25 ROwen	Updated test case to final msg interface;
					modified test case to handle message data as a dict
2003-10-30 ROwen	Modified to use TUI.Sound.
2004-05-18 ROwen	Stopped importing time; it wasn't used.
					Eliminated redundant imports in the test code.
2004-06-22 ROwen	Modified for RO.Keyvariable.KeyCommand->CmdVar
2004-08-11 ROwen	Modified for updated RO.Wdg.CtxMenu.
2005-08-02 ROwen	Modified for TUI.Sounds->TUI.PlaySound.
"""
import Tkinter
import RO.CnvUtil
import RO.KeyVariable
import RO.Wdg
import TUI.TUIModel
import TUI.PlaySound

def addWindow(tlSet):
	# about window
	tlSet.createToplevel(
		name = "Misc.Message",
		defGeom = "390x213+367+334",
		resizable = True,
		visible = True,
		wdgFunc = MessageWdg,
	)

_HelpPage = "Misc/MessageWin.html"

class MessageWdg(Tkinter.Frame):
	"""Instant messaging widget	
	"""
	def __init__(self,
		master,
		maxLines=100,
		**kargs
	):
		"""Inputs:
		- master: master widget
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)
		
		tuiModel = TUI.TUIModel.getModel()
		self.dispatcher = tuiModel.dispatcher

		self.maxLineIndex = maxLines + 1
		
		# create the widgets and connect the scrollbar
		self.yscroll = Tkinter.Scrollbar (
			master = self,
			orient = "vertical",
		)
		self.outText = Tkinter.Text (
			master = self,
			yscrollcommand = self.yscroll.set,
			wrap = "word",
			)
		self.yscroll.configure(command=self.outText.yview)
		self.outText.grid(row=0, column=0, sticky="nsew")
		self.yscroll.grid(row=0, column=1, sticky="nsew")

		self.inText = Tkinter.Text(
			master = self,
			height=3,
			wrap = "word",
			takefocus=True,
		)
		self.inText.grid(row=1, column=0, columnspan=2, sticky=Tkinter.NSEW)
		self.inText.focus_set()
		
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		
		# add help
		RO.Wdg.addCtxMenu(self.outText, helpURL=_HelpPage)
		RO.Wdg.addCtxMenu(self.inText, helpURL=_HelpPage)
			
		# add bindings
		RO.Wdg.Bindings.makeReadOnly(self.outText)
		self.inText.bind('<KeyPress-Return>', self.doSend)
		
		# create a keyvar to monitor the message keyword
		# the returned items are:
		# - date: in ISO format (e.g. 2003-06-25T23:53:12)
		# - message
		msgVar = RO.KeyVariable.KeyVar (
			keyword = "msg",
			actor = "msg",
			nval = 2,
			converters = str,
			dispatcher = self.dispatcher,
		)
		msgVar.addCallback(self.addOutput, callNow=False)

	def doSend(self, *args, **kargs):
		# obtain the message and clear the display
		# note that the message is always \n-terminated
		msgStr = self.inText.get("0.0", "end")[:-1]
		self.inText.delete("0.0", "end")
		cmdVar = RO.KeyVariable.CmdVar (
			cmdStr = "%s" % (msgStr,),
			actor = "msg",
		)
		self.dispatcher.executeCmd(cmdVar)
		return "break"
	
	def addOutput(self, msgData, isCurrent=True, keyVar=None):
		"""Add a line of data to the log.
		
		Inputs:
		- msgData: consists of two entities:
			- msgDate: the time the message was sent
			- msgStr: the message data (already \n-terminated)
		- category: name of category or None if no category
		"""
		# set auto-scroll flag true if scrollbar is at end
		# testing len(scrollPos works around an odd bug or misfeature
		# whereby if the window is not yet painted,
		# scrollPos is (0.0, 0.0, 0.0, 0.0)
		if not isCurrent:
			return
		if None in msgData:
			return
		if keyVar:
			cmdr = keyVar.getMsgDict()["cmdr"]
		else:
			cmdr = ""
		msgDate, msgStr = msgData
		msgTime = msgDate[11:]

		scrollPos = self.yscroll.get()
		doAutoScroll = len(scrollPos) != 2 or scrollPos[1] == 1.0
		self.outText.insert("end", "%s " % (msgTime,), ("time",))
		self.outText.insert("end", "%s: %s\n" % (cmdr, msgStr))
		TUI.PlaySound.msgReceived()
		extraLines = int(float(self.outText.index("end")) - self.maxLineIndex)
		if extraLines > 0:
			self.outText.delete("1.0", str(extraLines) + ".0")
		if doAutoScroll:
			self.outText.see("end")

if __name__ == "__main__":
	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher
	
	testFrame = MessageWdg(root)
	testFrame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	
	dataList = (
		("calvin", "2003-06-25T23:53:12", "How's the weather tonight?"),
		("hobbes", "2003-06-25T23:53:47", "Not bad, but we're just about out of tuna; I'm not sure I'll make it through our observing run."),
	)
	for cmdr, msgTime, msgStr in dataList:
		msgDict = {"cmdr":cmdr, "cmdID":11, "actor":"msg", "type":":",
			"data":{"msg": (msgTime, msgStr)}}
		kd.dispatch(msgDict)
	root.mainloop()
