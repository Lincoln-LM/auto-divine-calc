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
    includes += [
        "Xlib.X",
        "Xlib.XK",
        "Xlib.Xatom",
        "Xlib.Xcursorfont",
        "Xlib.Xutil",
        "Xlib.display",
        "Xlib.error",
        "Xlib.ext",
        "Xlib.ext.composite",
        "Xlib.ext.damage",
        "Xlib.ext.dpms",
        "Xlib.ext.ge",
        "Xlib.ext.nvcontrol",
        "Xlib.ext.randr",
        "Xlib.ext.record",
        "Xlib.ext.res",
        "Xlib.ext.screensaver",
        "Xlib.ext.security",
        "Xlib.ext.shape",
        "Xlib.ext.xfixes",
        "Xlib.ext.xinerama",
        "Xlib.ext.xinput",
        "Xlib.ext.xtest",
        "Xlib.keysymdef",
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
        "Xlib.protocol",
        "Xlib.protocol.display",
        "Xlib.protocol.event",
        "Xlib.protocol.request",
        "Xlib.protocol.rq",
        "Xlib.protocol.structs",
        "Xlib.rdb",
        "Xlib.support",
        "Xlib.support.connect",
        "Xlib.support.lock",
        "Xlib.support.unix_connect",
        "Xlib.support.vms_connect",
        "Xlib.threaded",
        "Xlib.xauth",
        "Xlib.xobject",
        "Xlib.xobject.colormap",
        "Xlib.xobject.cursor",
        "Xlib.xobject.drawable",
        "Xlib.xobject.fontable",
        "Xlib.xobject.icccm",
        "Xlib.xobject.resource",
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
