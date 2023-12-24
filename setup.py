import pkgutil
import sys
from contextlib import suppress

with suppress(ImportError):
    import pynput.keyboard
    import pynput.mouse
from cx_Freeze import Executable, setup

includes = [
    "pynput.keyboard." + sub.name
    for sub in pkgutil.iter_modules(pynput.keyboard.__path__)
] + ["pynput.mouse." + sub.name for sub in pkgutil.iter_modules(pynput.mouse.__path__)]

if sys.platform == "linux":
    import Xlib.keysymdef

    includes += [
        "Xlib.keysymdef." + sub.name
        for sub in pkgutil.iter_modules(Xlib.keysymdef.__path__)
    ]


build_exe_options = {
    "excludes": [],  # TODO
    "includes": includes,
    "zip_include_packages": [],  # TODO
    "build_exe": "dist",
}

setup(
    name="auto_divine_calc",
    description="Automatic Divine Travel Calculator",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            target_name="auto_divine_calc",
            icon=None,  # TODO
        )
    ],
)
