REM C:\Python34\Lib\site-packages\PyInstaller\hooks\hook-kivy.py must be replaced by the copy in this folder
rmdir /s /q "dist"
del "Snu Photo Manager Installer v0.9.exe"
python -m PyInstaller -w "Snu Photo Manager.spec"
del "dist\Snu Photo Manager\libgstreamer-1.0-0.dll"
del "dist\Snu Photo Manager\libglib-2.0-0.dll"
del "dist\Snu Photo Manager\libmikmod-2.dll"
del "dist\Snu Photo Manager\libmodplug-1.dll"
mkdir "dist\Snu Photo Manager\resizablebehavior"
xcopy "D:\personal\Projects\Snu Photo Manager\resizablebehavior\*.png" "dist\Snu Photo Manager\resizablebehavior\"
xcopy "D:\personal\Projects\Snu Photo Manager\borders" "dist\Snu Photo Manager\borders\" /s/e
xcopy "C:\Python34\Lib\site-packages\ffpyplayer-4.0.1.dev0-py3.4-win-amd64.egg\ffpyplayer" "dist\Snu Photo Manager\ffpyplayer\" /s/e
xcopy "installer.nsi" "dist\Snu Photo Manager\"
"C:\Program Files (x86)\NSIS\makensis.exe" "dist\Snu Photo Manager\installer.nsi"
move "dist\Snu Photo Manager\Snu Photo Manager Installer v0.9.exe" .
rmdir /s /q "build"
cmd /k