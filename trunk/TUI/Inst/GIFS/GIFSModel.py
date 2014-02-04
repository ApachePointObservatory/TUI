#!/usr/bin/env python
"""An object that models the current state of SPIcam.

2007-05-22 ROwen    Placeholder with some guesses as to keyword variables.
2007-05-24 ROwen    Added corrections submitted by Craig Loomis.
2007-06-07 ROwen    Removed unsupported ccdHeaters and ccdTemps keywords.
"""
from RO.CnvUtil import asFloatOrNone, asInt, asBool
import RO.Wdg
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
        self.actor = "gifs"
        self.dispatcher = tuiModel.dispatcher
        self.timelim = _TimeLim

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = 1,
            dispatcher = self.dispatcher,
        )

        configKeyFactory = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = (1, None), # why does (0, None fail?)
            dispatcher = self.dispatcher,
            description="Named positions for this device",
        )

        statusKeyFactory = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = (asBool, str, asFloatOrNone, asFloatOrNone),
            nval = 4,
            dispatcher = self.dispatcher,
            description="""Fields are:
                * is moving?
                * current position (a name or float)
                * destination position
                * estimated time to arrive (sec)
            """,
        )

        self.ccdTemp = keyVarFact(
            keyword = "ccdTemp",
            converters = asFloatOrNone,
            description = "CCD temperature (K)",
        )

        self.heaterPower = keyVarFact(
            keyword = "heaterPower",
            converters = asFloatOrNone,
            description = "Heater power (%)",
        )

        # no calMirrorConfig: options are "in", "out"

        self.collimatorConfig = configKeyFactory(
            keyword = "collimatorConfig",
        )

        self.disperserConfig = configKeyFactory(
            keyword = "disperserConfig",
        )

        # filterPos instead of filterConfig; it is output multiple times: once per filterwheel slot
        self.filterPos = keyVarFact(
            keyword = "filterPos",
            converters = (asInt, str, asFloatOrNone, asFloatOrNone, asFloatOrNone),
            nval = 5,
            description = """Details about one availabler filter
            * filterwheel slot (1-6)
            * filter name
            * central wavelength (Angstroms)
            * bandpass: bandpass (Angstroms)
            * focus offset (motor steps)
            """,
            refreshCmd = "filterwheel getConfig",
        )

        self.lensletsConfig = configKeyFactory(
            keyword="lensletsConfig",
        )

        self.magnifierConfig = configKeyFactory(
            keyword = "magnifierConfig",
        )

        self.calMirrorStatus = keyVarFact(
            keyword="calMirrorStatus",
            converters = (str, str),
            nval = 2,
            description = """calMirror status
            * preset name: one of "in", "out", apparently
            * position: ???
            """,
        )

        self.collimatorStatus = statusKeyFactory(keyword="collimatorStatus")

        self.filterStatus = keyVarFact(
            keyword = "filterStatus",
            converters = (asBool, asFloatOrNone, asFloatOrNone, str, asFloatOrNone, asFloatOrNone, asFloatOrNone),
            nval = 7,
            description = """Filter status
            * is moving?
            * filter slot (1-6 but a float for some reason)
            * filterwheel position (motor steps)
            * filter name
            * central wavelength (Angstroms)
            * bandpass (Angstroms)
            * focus offset (motor steps)
            """,
        )

        self.disperserStatus = statusKeyFactory(keyword="disperserStatus")

        self.lensletsStatus = statusKeyFactory(keyword="lensletsStatus")

        self.magnifierStatus = statusKeyFactory(keyword="magnifierStatus")

        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()
