#!/usr/bin/env python
"""An object that models the current state of SPIcam.

2007-05-22 ROwen    Placeholder with some guesses as to keyword variables.
2007-05-24 ROwen    Added corrections submitted by Craig Loomis.
2007-06-07 ROwen    Removed unsupported ccdHeaters and ccdTemps keywords.
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
                * destination name or position
                * destination position
                * position error (remaining distance to move when moving)
                * estimated time to arrive (sec) (0 when not moving)
            """,
        )
        presetsKeyFactory = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = (1, None),
            dispatcher = self.dispatcher,
            description="""Stage setting for the preset named in presetNames""",
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
        self.filterWavelengths = keyVarFact(
            keyword = "filterWavelengths",
            converters = asFloatOrNone,
            nval = (1, None),
            description = "Filter wavelengths (Angstroms), in slot order",
        )
        self.filterBandpasses = keyVarFact(
            keyword = "filterBandpasses",
            converters = asFloatOrNone,
            nval = (1, None),
            description = "Filter bandpasses (Angstroms), in slot order",
        )
        self.filterWavelengths = keyVarFact(
            keyword = "filterWavelengths",
            converters = asFloatOrNone,
            nval = (1, None),
            description = "Filter wavelengths (Angstroms), in slot order",
        )
        self.filterFocusOffsets = keyVarFact(
            keyword = "filterFocusOffsets",
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
            converters = (str, str),
            nval = 2,
            description = """calMirror status
            * preset name: one of "in", "out", apparently
            * position: ???
            """,
        )
        self.collimatorStatus = statusKeyFactory(keyword="collimatorStatus")
        self.disperserStatus = statusKeyFactory(keyword="disperserStatus")
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
        self.lensletsStatus = statusKeyFactory(keyword="lensletsStatus")
        self.magnifierStatus = statusKeyFactory(keyword="magnifierStatus")

        self.presetNames = presetsKeyFactory(keyword="presetNames", description="List of preset names")
        self.presetCalMirrors = presetsKeyFactory(keyword="presetCalMirrors")
        self.presetCollimators = presetsKeyFactory(keyword="presetCollimators")
        self.presetDispersers = presetsKeyFactory(keyword="presetDispersers")
        self.presetFilters = presetsKeyFactory(keyword="presetFilters")
        self.presetLenslets = presetsKeyFactory(keyword="presetLenslets")
        self.presetMagnifiers = presetsKeyFactory(keyword="presetMagnifiers")

        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()
