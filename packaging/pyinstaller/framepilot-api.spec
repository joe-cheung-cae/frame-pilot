# -*- mode: python ; coding: utf-8 -*-
# One-dir sidecar named framepilot-api.
# Windows packaged builds should use --loop asyncio when uvloop is absent
# (sidecar_main already selects asyncio on Windows).

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

repo_root = Path(SPECPATH).resolve().parents[1]
api_root = repo_root / "apps" / "api"

hiddenimports = [
    "app.main",
    "app.sidecar_main",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "httptools",
    "sqlalchemy.dialects.sqlite",
    "PIL.JpegImagePlugin",
    "PIL.PngImagePlugin",
    "PIL.WebPImagePlugin",
    "imagehash",
    "numpy",
]
hiddenimports += collect_submodules("scipy")

a = Analysis(
    [str(api_root / "app" / "sidecar_main.py")],
    pathex=[str(api_root)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[str(Path(SPECPATH) / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="framepilot-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="framepilot-api",
)
