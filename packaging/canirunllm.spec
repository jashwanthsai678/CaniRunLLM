# PyInstaller spec for the standalone desktop build.
#
# Build from the project root with:
#   pyinstaller packaging/canirunllm.spec --noconfirm
#
# Output: dist/CanIRunLLM.exe - a single self-contained file. It
# self-extracts to a temp directory at startup (a few seconds slower
# to launch than a onedir build), but matches the "download one file,
# double-click it" experience the desktop build is meant to give.

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

PROJECT_ROOT = Path(SPECPATH).resolve().parent
SRC = PROJECT_ROOT / "src"

datas = [
    (str(SRC / "canirunllm" / "registry" / "models.json"),
     "canirunllm/registry"),
    (str(SRC / "canirunllm" / "web" / "static"),
     "canirunllm/web/static"),
    (str(SRC / "canirunllm" / "web" / "templates"),
     "canirunllm/web/templates"),
]

hiddenimports = []
binaries = []

for package in ("uvicorn", "fastapi", "starlette", "pydantic", "pydantic_core", "GPUtil"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["desktop_launcher.py"],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="CanIRunLLM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
