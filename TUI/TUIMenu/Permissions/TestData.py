import TUI.Base.TestDispatcher

tester = TUI.Base.TestDispatcher.TestDispatcher(actor="perms", delay=0.5)

MainData = (
    "actors=dis, echelle, tcc, tlamps, tspec",
    "programs=UW01, CL01, TU01",
    "lockedActors=tspec",
    "authList=TU01, echelle, perms, tcc, tspec",
    "authList=CL01, tcc, dis, tspec, tlamps",
    "authList=UW01, tcc, echelle",
)

AnimDataSet = (
    (
        "authList=CL01, tcc, dis, echelle, tspec, tlamps",
        "authList=UW01, tcc, tspec, tlamps",
    ),
    (
        "programs=TU01, UW01",
    ),
    (
        "actors=tcc, tspec, dis, echelle, tlamps, apollo",
    ),
    (
        "authList=CL01, apollo, echelle, perms, tcc, tspec",
    ),
)
