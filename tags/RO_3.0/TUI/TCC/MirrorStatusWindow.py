#!/usr/bin/env python
"""Displays the status of the mirrors.

2003-03-25 ROwen    first release
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-06-09 ROwen    Removed most args from addWindow
                    and dispatcher arg from MirrorStatsuWdg.
2003-06-25 ROwen    Fixed a keyword name error in the test case;
                    modified test case to handle message data as a dict.
2003-07-13 WKetzeback   Added commanded positions to the widget.
2003-07-22 ROwen    Modified to use gridder; abbreviated displayed labels
2003-12-16 ROwen    Fixed comments for addWindow.
2004-05-18 ROwen    Stopped importing string and sys since they weren't used.
2006-09-27 ROwen    Updated for new 5-axis secondary.
2010-09-24 ROwen    Modified to get keyVars from TCC model (now that they are available).
                    Added WindowName constant.
2011-06-17 ROwen    Changed "type" to "msgType" in parsed message dictionaries (in test code only).
"""
import Tkinter
import RO.Wdg
import TUI.TUIModel
import TUI.TCC.TCCModel

WindowName = "TCC.Mirror Status"

NumSecAxes = 5
NumTertAxes = 3

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+22",
        visible = False,
        resizable = False,
        wdgFunc = MirrorStatusWdg,
    )

class MirrorStatusWdg (Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """creates a new mirror status display frame

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        
        tuiModel = TUI.TUIModel.getModel()
        tccModel = TUI.TCC.TCCModel.getModel()
        dispatcher = tuiModel.dispatcher
        gr = RO.Wdg.Gridder(self)

        refreshCmd = "mirror status"

        #
        # display mirror orientation
        #
        
        # orientation title, (precision, width) for each column
        orientColInfo = (
            (u"Piston (\N{MICRO SIGN}m)", (2, 10)),
            ("X Tilt (\")",               (2, 10)),
            ("Y Tilt (\")",               (2, 10)),
            (u"X Trans (\N{MICRO SIGN}m)", (2, 10)),
            (u"Y Trans (\N{MICRO SIGN}m)", (2, 10)),
        )
        
        orientTitles, orientPrecWidthSet = zip(*orientColInfo)

        orientTitleWdgs = [RO.Wdg.StrLabel(self, text=label) for label in orientTitles]
        gr.gridWdg(
            label = "Orientation",
            dataWdg = orientTitleWdgs,
        )
        
        # label text, keyword prefix for each row
        orientNumLabelPrefix = (
            (NumSecAxes, "Sec act", "sec"),
            (NumSecAxes, "Sec des", "secDes"),
            (NumTertAxes, "Tert act", "tert"),
            (NumTertAxes, "Tert des", "tertDes"),
        )

        # for each mirror, create a set of widgets find the associated keyvar
        for numAxes, niceName, keyPrefix in orientNumLabelPrefix:
            orientWdgSet = [RO.Wdg.FloatLabel(self,
                    precision = prec,
                    width = width,
                ) for prec, width in orientPrecWidthSet[0:numAxes]
            ]
            gr.gridWdg (
                label = niceName,
                dataWdg = orientWdgSet
            )

            orientVar = getattr(tccModel, "%sOrient" % (keyPrefix,))
            orientVar.addROWdgSet(orientWdgSet)

        # divider
        gr.gridWdg(
            label = False,
            dataWdg = Tkinter.Frame(self, height=1, bg="black"),
            colSpan = len(orientColInfo) + 1,
            sticky = "ew",
        )
        
        #
        # display mirror mount data
        #
        
        # mount title
        axisTitles = ["%c (steps)" % (ii + ord("A"),) for ii in range(max(NumSecAxes, NumTertAxes))]
        axisTitleWdgs = [RO.Wdg.StrLabel(self, text=label) for label in axisTitles]
        gr.gridWdg(
            label = "Mount",
            dataWdg = axisTitleWdgs,
        )

        # width
        mountWidth = 10

        # label text, keyword prefix for each row
        mountNumLabelPrefix = (
            (NumSecAxes,  "Sec act", "secAct"),
            (NumSecAxes,  "Sec cmd", "secCmd"),
            (NumTertAxes, "Tert act", "tertAct"),
            (NumTertAxes, "Tert cmd", "tertCmd"),
        )
        
        # for each mirror, create a set of widgets and a key variable
        for numAxes, niceName, keyPrefix in mountNumLabelPrefix:
            mountWdgSet = [RO.Wdg.FloatLabel(self,
                    precision = 0,
                    width = mountWidth,
                ) for ii in range(numAxes)
            ]
            gr.gridWdg (
                label = niceName,
                dataWdg = mountWdgSet,
            )

            mountVar = getattr(tccModel, "%sMount" % (keyPrefix,))
            mountVar.addROWdgSet(mountWdgSet)


if __name__ == "__main__":
    root = RO.Wdg.PythonTk()

    kd = TUI.TUIModel.getModel(True).dispatcher

    testFrame = MirrorStatusWdg (root)
    testFrame.pack()

    dataDict = {
        "SecDesOrient": (105.16, -54.99, -0.90, -0.35, 21.15), 
        "SecCmdMount": (725528., 356362., 671055., 54300, 32150), 
        "SecActMount": (725550., 356400., 673050., 54321, 32179), 
        "SecOrient": (105.26, -55.01, -0.95, -0.15, 21.05), 

        "TertDesOrient": (205.16, 54.99, 0.90, 0.35, -21.15), 
        "TertCmdMount": (825528., 456362., 771055.), 
        "TertActMount": (825550., 456400., 773050.), 
        "TertOrient": (205.26, 55.01, 0.95, 0.15, -21.05), 
    }
    msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "msgType":":", "data":dataDict}
    kd.dispatch(msgDict)

    root.mainloop()
