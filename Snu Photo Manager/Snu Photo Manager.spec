# -*- mode: python -*-

block_cipher = None


a = Analysis(['D:\\personal\\Projects\\Snu Photo Manager\\main.py'],
             pathex=['C:\\Python34\\share\\ffpyplayer\\ffmpeg\\bin', 'C:\\Python34\\share\\gstreamer\\bin', 'C:\\Python34\\share\\sdl2\\bin', 'D:\\personal\\Projects\\Snu Photo Manager\\Snu Photo Manager'],
             binaries=[],
             datas=[],
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
          strip=False,
          upx=True,
          console=True , icon='D:\\personal\\Projects\\Snu Photo Manager\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Snu Photo Manager')
