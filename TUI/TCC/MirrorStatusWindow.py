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
2014-07-21 ROwen    Changed mount section for new TCC: show commanded actuator length,
                    measured encoder length and desired encoder length.
                    Added help text and a status bar to dispay it.
                    Removed some unused variables.
"""
import Tkinter
import RO.Wdg
import TUI.TCC.TCCModel

WindowName = "TCC.Mirror Status"

NumSecAxes = 5
NumTertAxes = 3

_HelpURL = "Telescope/MirrorStatus.html"

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
        
        tccModel = TUI.TCC.TCCModel.getModel()
        gr = RO.Wdg.Gridder(self)

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
        
        # data for orientation table layout: number of axes, label text, keyword prefix, help text
        orientNumLabelPrefixHelpList = (
            (NumSecAxes, "Sec orient", "sec", "secondary measured orienation"),
            (NumSecAxes, "Sec des", "secDes", "secondary desired orientation"),
            (NumTertAxes, "Tert orient", "tert", "tertiary measured orientation"),
            (NumTertAxes, "Tert des", "tertDes", "tertiary desired orientation"),
        )

        # for each mirror, create a set of widgets find the associated keyvar
        for numAxes, niceName, keyPrefix, helpText in orientNumLabelPrefixHelpList:
            keyVarName = "%sOrient" % (keyPrefix,)
            orientWdgSet = [RO.Wdg.FloatLabel(self,
                    precision = prec,
                    width = width,
                    helpText = "%s (%s)" % (helpText, keyVarName,),
                    helpURL = _HelpURL,
                ) for prec, width in orientPrecWidthSet[0:numAxes]
            ]
            gr.gridWdg (
                label = niceName,
                dataWdg = orientWdgSet
            )

            orientVar = getattr(tccModel, keyVarName)
            orientVar.addROWdgSet(orientWdgSet)

        # divider
        gr.gridWdg(
            label = False,
            dataWdg = Tkinter.Frame(self, height=1, bg="black"),
            colSpan = len(orientColInfo) + 1,
            sticky = "ew",
        )
        
        #
        # display mirror encoder data
        #
        
        # mount title
        axisTitles = [u"%c (steps)" % (ii + ord("A"),) for ii in range(max(NumSecAxes, NumTertAxes))]
        axisTitleWdgs = [RO.Wdg.StrLabel(self, text=label) for label in axisTitles]
        gr.gridWdg(
            label = "Mount",
            dataWdg = axisTitleWdgs,
        )

        # width
        mountWidth = 10

        # data for mount table layout: number of axes, label text, keyword prefix, help text
        mountNumLabelPrefixHelpList = (
            (NumSecAxes,  "Sec enc",      "secEnc", "secondary measured encoder length"),
            (NumSecAxes,  "Sec des enc",  "secDesEnc", "secondary desired encoder length"),
            (NumSecAxes,  "Sec cmd",      "secCmd", "secondary commanded actuator length"),
            (NumTertAxes, "Tert enc",     "tertEnc", "tertiary measured encoder length"),
            (NumTertAxes, "Tert des enc", "tertDesEnc", "tertiary desired encoder length"),
            (NumTertAxes, "Tert cmd",     "tertCmd", "tertiary commanded actuator length"),
        )
        
        # for each mirror, create a set of widgets and a key variable
        for numAxes, niceName, keyPrefix, helpText in mountNumLabelPrefixHelpList:
            keyVarName = "%sMount" % (keyPrefix,)
            mountWdgSet = [RO.Wdg.FloatLabel(self,
                    precision = 0,
                    width = mountWidth,
                    helpText = "%s (%s)" % (helpText, keyVarName),
                    helpURL = _HelpURL,
                ) for ii in range(numAxes)
            ]
            gr.gridWdg (
                label = niceName,
                dataWdg = mountWdgSet,
            )

            mountVar = getattr(tccModel, keyVarName)
            mountVar.addROWdgSet(mountWdgSet)

        self.statusWdg = RO.Wdg.StatusBar(self)
        gr.gridWdg(False, self.statusWdg, colSpan=6, sticky="ew")


if __name__ == "__main__":
    import TUI.TUIModel
    root = RO.Wdg.PythonTk()

    kd = TUI.TUIModel.getModel(True).dispatcher

    testFrame = MirrorStatusWdg(root)
    testFrame.pack()

    dataDict = {
        "SecDesOrient": (105.16, -54.99, -0.90, -0.35, 21.15),
        "SecCmdMount": (725528., 356362., 671055., 54300, 32150),
        "SecOrient": (105.26, -55.01, -0.95, -0.15, 21.05),
        "SecEncMount": (725572., 356301., 671032., 54332, 32112),
        "SecDesEncMount": (725509., 356327., 679956., 54385, 32154),

        "TertDesOrient": (205.16, 54.99, 0.90, 0.35, -21.15),
        "TertCmdMount": (825528, 456362, 771055),
        "TertOrient": (205.26, 55.01, 0.95, 0.15, -21.05),
        "TertEncMount": (825587, 456318, 771009),
        "TertDesEncMount": (825511, 456373, 771033),
    }
    msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "msgType":":", "data":dataDict}
    kd.dispatch(msgDict)

    root.mainloop()
