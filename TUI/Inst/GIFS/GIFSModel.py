#!/usr/bin/env python
"""An object that models the current state of GIFS.

2014-02-25 ROwen
"""
from RO.CnvUtil import asFloatOrNone, asBool
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
            converters = (asBool, str, str, asFloatOrNone, asFloatOrNone, asFloatOrNone),
            nval = 6,
            dispatcher = self.dispatcher,
            description="""Status about a stage. Sent once at the start of a move
                and at least once at the end of a move. Fields are:
                * is moving?
                * current name or position
                * commanded name or position
                * commanded position as a number
                * position error = measured - commanded position;
                  when starting a move this is the negative of the distance to be moved
                * estimated time to arrive (sec) (0 when not moving)
            """,
        )
        presetsKeyFactory = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = (1, None),
            dispatcher = self.dispatcher,
            description="""Stage setting for the preset named in namePresets""",
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
        self.filterNames = keyVarFact(
            keyword = "filterNames",
            converters = str,
            nval = (1, None),
            description = "Filter names, in slot order",
        )
        self.filterCenters = keyVarFact(
            keyword = "filterCenters",
            converters = asFloatOrNone,
            nval = (1, None),
            description = "Filter central wavelengths (Angstroms), in slot order",
        )
        self.filterWidths = keyVarFact(
            keyword = "filterWidths",
            converters = asFloatOrNone,
            nval = (1, None),
            description = "Filter bandpass widths (Angstroms), in slot order",
        )
        self.filterFocus = keyVarFact(
            keyword = "filterFocus",
            converters = asFloatOrNone,
            nval = (1, None),
            description = "Filter focus offsets (motor steps), in slot order",
        )
        self.lensletsConfig = configKeyFactory(
            keyword="lensletsConfig",
        )
        self.magnifierConfig = configKeyFactory(
            keyword = "magnifierConfig",
        )

        self.calMirrorStatus = keyVarFact(
            keyword="calMirrorStatus",
            converters = (asBool, str, str, asFloatOrNone),
            nval = 4,
            description = """calMirror status
            * isMoving
            * preset name: one of "in", "out", apparently
            * position: ???
            * estimated time to arrive (sec) (0 when not moving)
            """,
        )
        self.collimatorStatus = statusKeyFactory(keyword="collimatorStatus")
        self.disperserStatus = statusKeyFactory(keyword="disperserStatus")
        self.filterStatus = keyVarFact(
            keyword = "filterStatus",
            converters = (asBool, asFloatOrNone, asFloatOrNone, str, asFloatOrNone, asFloatOrNone, asFloatOrNone, asFloatOrNone),
            nval = 8,
            description = """Filter status
            * is moving?
            * filter slot (1-6 but a float for some reason)
            * filterwheel position (motor steps)
            * filter name
            * central wavelength (Angstroms)
            * bandpass (Angstroms)
            * focus offset (motor steps)
            * estimated time to arrive (sec) (0 when not moving)
            """,
        )
        self.lensletsStatus = statusKeyFactory(keyword="lensletsStatus")
        self.magnifierStatus = statusKeyFactory(keyword="magnifierStatus")

        self.namePresets = presetsKeyFactory(keyword="namePresets", description="List of preset names")
        self.calMirrorPresets = presetsKeyFactory(keyword="calMirrorPresets")
        self.collimatorPresets = presetsKeyFactory(keyword="collimatorPresets")
        self.disperserPresets = presetsKeyFactory(keyword="disperserPresets")
        self.filterPresets = presetsKeyFactory(keyword="filterPresets")
        self.lensletPresets = presetsKeyFactory(keyword="lensletPresets")
        self.magnifierPresets = presetsKeyFactory(keyword="magnifierPresets")

        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()
