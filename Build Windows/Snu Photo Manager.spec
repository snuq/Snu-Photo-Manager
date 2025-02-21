from kivy_deps import sdl2, glew, ffpyplayer
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['..\\main.py'],
             pathex=[],
             binaries=[],
             datas=[('..\\resizablebehavior\*.png', '.\\resizablebehavior'), ('..\\borders', '.\\borders'), ('..\\data\\*.*', '.\\data\\'), ('..\\icon.ico', '.'), ('..\\about.txt', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Snu Photo Manager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          contents_directory='.',
          console=False,
          icon='..\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (ffpyplayer.dep_bins + sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='Snu Photo Manager')
