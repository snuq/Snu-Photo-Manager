#from kivy.deps import sdl2, glew, ffpyplayer
# -*- mode: python -*-

block_cipher = None

#from kivy.tools.packaging.pyinstaller_hooks import install_hooks
#install_hooks(globals())

def filter_binaries(all_binaries):
    print('Excluding system libraries')
    import subprocess
    excluded_pkgs  = set()
    excluded_files = set()
    whitelist_prefixes = ('libpython3.5', 'python-')
    binaries = []

    for b in all_binaries:
        try:
            output = subprocess.check_output(['dpkg', '-S', b[1]], stderr=open('/dev/null'))
            p, path = output.split(':', 2)
            if not p.startswith(whitelist_prefixes):
                excluded_pkgs.add(p)
                excluded_files.add(b[0])
                print(' excluding {f} from package {p}'.format(f=b[0], p=p))
        except Exception:
            pass

    print('Your exe will depend on the following packages:')
    print(excluded_pkgs)

    inc_libs = set(['libpython3.5.so.1.0'])
    binaries = [x for x in all_binaries if x[0] not in excluded_files]
    return binaries

binexcludes = [
     'gobject', 'gio', 'gtk', 'gi', 'wx',
]

a = Analysis(['/home/kivy/Snu Photo Manager/main.py'],
             pathex=['/home/kivy/Snu Photo Manager/Snu Photo Manager'],
             binaries=[],
             datas=[('/home/kivy/Snu Photo Manager/data/*.*', './data/'), ('/home/kivy/Snu Photo Manager/about.txt', '.'), ('/home/kivy/Snu Photo Manager/icon.ico', '.'), ('/home/kivy/Snu Photo Manager/*.kv', '.')],
             hiddenimports=[],
             excludes=binexcludes,
             hookspath=[],
             runtime_hooks=[],
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
          console=False,
          icon='/home/kivy/Snu Photo Manager/icon.ico')

binaries = filter_binaries(a.binaries)

coll = COLLECT(exe,
               binaries,
               a.zipfiles,
               a.datas,
               #*[Tree(p) for p in (ffpyplayer.dep_bins + sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='Snu Photo Manager')
