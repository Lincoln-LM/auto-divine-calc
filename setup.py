import sys

from cx_Freeze import Executable, setup

includes = [
    "pynput.keyboard._base",
    "pynput.keyboard._darwin",
    "pynput.keyboard._dummy",
    "pynput.keyboard._uinput",
    "pynput.keyboard._win32",
    "pynput.keyboard._xorg",
    "pynput.mouse._base",
    "pynput.mouse._darwin",
    "pynput.mouse._dummy",
    "pynput.mouse._win32",
    "pynput.mouse._xorg",
]

if sys.platform == "linux":
    includes += (
        "Xlib.keysymdef.apl",
        "Xlib.keysymdef.arabic",
        "Xlib.keysymdef.cyrillic",
        "Xlib.keysymdef.greek",
        "Xlib.keysymdef.hebrew",
        "Xlib.keysymdef.katakana",
        "Xlib.keysymdef.korean",
        "Xlib.keysymdef.latin1",
        "Xlib.keysymdef.latin2",
        "Xlib.keysymdef.latin3",
        "Xlib.keysymdef.latin4",
        "Xlib.keysymdef.miscellany",
        "Xlib.keysymdef.publishing",
        "Xlib.keysymdef.special",
        "Xlib.keysymdef.technical",
        "Xlib.keysymdef.thai",
        "Xlib.keysymdef.xf86",
        "Xlib.keysymdef.xk3270",
        "Xlib.keysymdef.xkb",
    )


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
