"""A specialization of RO.Wdg.StripChart that adds methods to trace keyVars

History:
2010-10-01 ROwen
2010-12-23  Backward-incompatible changes:
            - Modified for backward-incompatible RO.Wdg.StripChartWdg
            - plotKeyVar no longer takes a "name" argument; use label if you want a name that shows up in legends.
"""
import RO.Wdg.StripChartWdg

TimeConverter = RO.Wdg.StripChartWdg.TimeConverter

class StripChartWdg(RO.Wdg.StripChartWdg.StripChartWdg):
    def plotKeyVar(self, subplotInd, keyVar, keyInd=0, func=None, **kargs):
        """Plot one value of one keyVar
        
        Inputs:
        - subplotInd: index of line on Subplot
        - keyVar: keyword variable to plot
        - keyInd: index of keyword variable to plot
        - func: function to transform the value; note that func will never receive None;
            if func is None then the data is not transformed
        **kargs: keyword arguments for StripChartWdg.addLine
        """
        line = self.addLine(subplotInd=subplotInd, **kargs)
        
        if func is None:
            func = lambda x: x
        
        def callFunc(valList, isCurrent, keyVar=None, line=line, keyInd=keyInd, func=func):
            if not isCurrent or not keyVar.isGenuine():
                return
            val = valList[keyInd]
            if val is None:
                return
            line.addPoint(func(val))
        
        keyVar.addCallback(callFunc, callNow=False)
