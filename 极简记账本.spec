# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('D:\\anaconda\\anaconda3\\envs\\python\\Library\\bin\\ffi.dll', '.'), ('D:\\anaconda\\anaconda3\\envs\\python\\Library\\bin\\libmpdec-4.dll', '.'), ('D:\\anaconda\\anaconda3\\envs\\python\\Library\\bin\\zstd.dll', '.'), ('D:\\anaconda\\anaconda3\\envs\\python\\Library\\bin\\liblzma.dll', '.'), ('D:\\anaconda\\anaconda3\\envs\\python\\Library\\bin\\LIBBZ2.dll', '.'), ('D:\\anaconda\\anaconda3\\envs\\python\\Library\\bin\\libssl-3-x64.dll', '.'), ('D:\\anaconda\\anaconda3\\envs\\python\\Library\\bin\\libexpat.dll', '.')],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='极简记账本',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:\\Users\\lin\\AppData\\Local\\Temp\\cda6eefa-0e6c-4856-a6cf-7949b36b9dbe',
)
