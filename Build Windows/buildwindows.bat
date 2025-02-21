rmdir /s /q "dist"
del "Snu Photo Manager Installer v0.9.exe"
C:\Python310\python -m PyInstaller "Snu Photo Manager.spec" --upx-dir=C:\Python310\upx
del "dist\Snu Photo Manager\cv2\opencv_videoio_ffmpeg440_64.dll"
del "dist\Snu Photo Manager\ucrtbase.dll"
xcopy "ucrtbase.dll" "dist\Snu Photo Manager\"
del "dist\Snu Photo Manager\VCRUNTIME140.dll"
xcopy "VCRUNTIME140.dll" "dist\Snu Photo Manager\"
xcopy "installer.nsi" "dist\Snu Photo Manager\"
"C:\Program Files (x86)\NSIS\makensis.exe" "dist\Snu Photo Manager\installer.nsi"
move "dist\Snu Photo Manager\Snu Photo Manager Installer v0.9.exe" .
rmdir /s /q "build"
cmd /k
