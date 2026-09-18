; Deniz Sideloader - Windows Installer (NSIS 3, per-user, no admin required)
; Built files: release\DenizSideloader\*  ->  release\DenizSideloader-<version>-Setup.exe

!include "MUI2.nsh"
!include "LogicLib.nsh"

!define APP_NAME "Deniz Sideloader"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Deniz Sideloader Contributors"
!define APP_URL "https://github.com/dbudakli1402-collab/DenizSideloader"
!define APP_EXE "DenizSideloader.exe"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\DenizSideloader"

Icon "..\assets\logo.ico"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "..\release\DenizSideloader-${APP_VERSION}-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\DenizSideloader"
RequestExecutionLevel user
ShowInstDetails nevershow
ShowUninstDetails nevershow

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "English"

Section "!$(^NameDA) $(^Name)" SEC_APP
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "..\release\DenizSideloader\*.*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${UNINST_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "${UNINST_KEY}" "URLInfoAbout" "${APP_URL}"
  WriteRegStr HKCU "${UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoRepair" 1
SectionEnd

Section "Startmenü-Eintrag" SEC_STARTMENU
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Deinstallieren.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section /o "Desktop-Verknüpfung" SEC_DESKTOP
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Deinstallieren.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "${UNINST_KEY}"
SectionEnd
