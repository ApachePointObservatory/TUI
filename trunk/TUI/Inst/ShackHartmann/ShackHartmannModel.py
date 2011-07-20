#!/usr/bin/env python
"""An object that models the current state of the Shack-Hartmann.

2011-07-20 ROwen
"""
import RO.CnvUtil
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for fairly fast commands;
_TimeLim = 80

_theModel = None

def getModel():
    global _theModel
    if _theModel == None:
        _theModel = _Model()
    return _theModel


class _Model (object):
    def __init__(self,
    **kargs):
        tuiModel = TUI.TUIModel.getModel()
        self.actor = "shack"
        self.dispatcher = tuiModel.dispatcher
        self.timelim = _TimeLim

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = 1,
            dispatcher = self.dispatcher,
        )
        
        self.shutter = keyVarFact(
            keyword = "shutter",
            nval = 1,
            description = "Current shutter state",
        )
        
        keyVarFact.setKeysRefreshCmd()
        
        self.ccdState = keyVarFact(
            keyword="ccdState",
            description="ccd state",
        )

        keyVarFact.setKeysRefreshCmd()
    


if __name__ == "__main__":
    getModel()
