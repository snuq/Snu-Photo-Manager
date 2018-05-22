!define VERSION "0.9"
SetCompressor lzma

; The name of the installer
Name "Snu Photo Manager ${VERSION}"

; The file to write
OutFile "Snu Photo Manager Installer v${VERSION}.exe"

; The default installation directory
InstallDir "$PROGRAMFILES64\Snu Photo Manager"

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Snu Photo Manager" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

AllowRootDirInstall true

Icon "icon.ico"


;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles


;--------------------------------

; The stuff to install
Section "!Snu Photo Manager (Required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; Put files there
  File /r *

  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\Snu Photo Manager" "Install_Dir" "$INSTDIR"

  SectionEnd
  
Section "Create Uninstaller"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Photo Manager" "DisplayName" "Snu Photo Manager"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Photo Manager" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Photo Manager" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Photo Manager" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Create Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\Snu Photo Manager"
  CreateShortcut "$SMPROGRAMS\Snu Photo Manager\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortcut "$SMPROGRAMS\Snu Photo Manager\Snu Photo Manager.lnk" "$INSTDIR\Snu Photo Manager.exe" "" "$INSTDIR\Snu Photo Manager.exe" 0
  
SectionEnd

Section /o "Create Desktop Shortcut"

  CreateShortcut "$DESKTOP\Snu Photo Manager.lnk" "$INSTDIR\Snu Photo Manager.exe" "" "$INSTDIR\Snu Photo Manager.exe" 0

SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Photo Manager"
  DeleteRegKey HKLM "SOFTWARE\Snu Photo Manager"

  ; Remove files and uninstaller
  Delete "$INSTDIR\*"
  Delete $INSTDIR\uninstall.exe

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\Snu Photo Manager\*.*"
  Delete "$DESKTOP\Snu Photo Manager.lnk"

  ; Remove directories used
  RMDir /r "$INSTDIR\docutils"
  RMDir /r "$INSTDIR\ffpyplayer"
  RMDir /r "$INSTDIR\include"
  RMDir /r "$INSTDIR\kivy_install"
  RMDir /r "$INSTDIR\lib2to3"
  RMDir /r "$INSTDIR\resizablebehavior"
  RMDir /r "$INSTDIR\tcl"
  RMDir /r "$INSTDIR\tk"
  RMDir /r "$INSTDIR\help"
  RMDir "$SMPROGRAMS\Snu Photo Manager"
  RMDir "$INSTDIR"

SectionEnd
