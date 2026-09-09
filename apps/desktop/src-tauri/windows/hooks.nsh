; NSIS installer hooks for leftover #198.
; Tauri copies files after NSIS_HOOK_PREINSTALL. The stock File dialog is
; Abort/Retry/Ignore — Ignore leaves a half-written framepilot-api\_internal
; tree (Joe's Win11 v2.1.2-desktop repro). Tauri CheckIfAppIsRunning only
; stops ${MAINBINARYNAME}.exe, not the PyInstaller sidecar that locks the DLLs.
;
; These hooks block until the shell, sidecar, and known _internal lock targets
; are free. The prompt is Retry/Cancel only (no Ignore). Cancel Aborts before
; any File copy. Silent/passive installs try one force-close, then Abort if
; still locked.
!include LogicLib.nsh

!macro FramePilotMarkImageRunning imageName flagVar
  nsis_tauri_utils::FindProcessCurrentUser "${imageName}"
  Pop $R0
  ${If} $R0 = 0
    StrCpy ${flagVar} 1
  ${Else}
    nsis_tauri_utils::FindProcess "${imageName}"
    Pop $R0
    ${If} $R0 = 0
      StrCpy ${flagVar} 1
    ${EndIf}
  ${EndIf}
!macroend

!macro FramePilotMarkFileLocked filePath flagVar
  ${If} ${FileExists} "${filePath}"
    ClearErrors
    FileOpen $R9 "${filePath}" a
    ${If} ${Errors}
      StrCpy ${flagVar} 1
    ${Else}
      FileClose $R9
    ${EndIf}
  ${EndIf}
!macroend

!macro FramePilotKillImage imageName
  nsis_tauri_utils::KillProcessCurrentUser "${imageName}"
  Pop $R0
  nsis_tauri_utils::KillProcess "${imageName}"
  Pop $R0
  ExecWait '"$SYSDIR\taskkill.exe" /F /T /IM ${imageName}' $R0
!macroend

!macro FramePilotKillInstallLockers
  ; Kill the desktop shell first so the sidecar supervisor cannot respawn
  ; framepilot-api.exe while we are unlocking _internal.
  !insertmacro FramePilotKillImage "${MAINBINARYNAME}.exe"
  !insertmacro FramePilotKillImage "FramePilot.exe"
  !insertmacro FramePilotKillImage "framepilot-api.exe"
  Sleep 1500
!macroend

!macro FramePilotTargetsAreLocked flagVar
  StrCpy ${flagVar} 0
  !insertmacro FramePilotMarkImageRunning "${MAINBINARYNAME}.exe" ${flagVar}
  !insertmacro FramePilotMarkImageRunning "FramePilot.exe" ${flagVar}
  !insertmacro FramePilotMarkImageRunning "framepilot-api.exe" ${flagVar}
  !insertmacro FramePilotMarkFileLocked "$INSTDIR\${MAINBINARYNAME}.exe" ${flagVar}
  !insertmacro FramePilotMarkFileLocked "$INSTDIR\FramePilot.exe" ${flagVar}
  !insertmacro FramePilotMarkFileLocked "$INSTDIR\framepilot-api\framepilot-api.exe" ${flagVar}
  !insertmacro FramePilotMarkFileLocked "$INSTDIR\framepilot-api\_internal\MSVCP140.dll" ${flagVar}
  !insertmacro FramePilotMarkFileLocked "$INSTDIR\framepilot-api\_internal\VCRUNTIME140.dll" ${flagVar}
!macroend

!macro FramePilotWaitForUnlockedTargets
  !define FP_LOCK_UID ${__LINE__}

  FramePilotLockCheck_${FP_LOCK_UID}:
    !insertmacro FramePilotTargetsAreLocked $R4
    ${If} $R4 = 0
      Goto FramePilotLockDone_${FP_LOCK_UID}
    ${EndIf}

    IfSilent FramePilotLockSilent_${FP_LOCK_UID} 0
    ${If} $PassiveMode = 1
      Goto FramePilotLockSilent_${FP_LOCK_UID}
    ${EndIf}

    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "FramePilot or the local API (framepilot-api) is still running, so this installer cannot replace files under framepilot-api\_internal.$\r$\n$\r$\nClose FramePilot (File -> Quit, or the window X), wait until it exits, then click Retry.$\r$\n$\r$\nCancel aborts this install and leaves the previous files unchanged.$\r$\n$\r$\nIf Windows later says 'Error opening file for writing', click Abort -- not Ignore. Ignore leaves a broken install." IDRETRY FramePilotLockRetry_${FP_LOCK_UID} IDCANCEL FramePilotLockCancel_${FP_LOCK_UID}

  FramePilotLockRetry_${FP_LOCK_UID}:
    !insertmacro FramePilotKillInstallLockers
    Goto FramePilotLockCheck_${FP_LOCK_UID}

  FramePilotLockSilent_${FP_LOCK_UID}:
    !insertmacro FramePilotKillInstallLockers
    !insertmacro FramePilotTargetsAreLocked $R4
    ${If} $R4 = 0
      Goto FramePilotLockDone_${FP_LOCK_UID}
    ${EndIf}
    Abort "FramePilot or framepilot-api is still running or has locked files under _internal. Close FramePilot (File -> Quit) and run the installer again."

  FramePilotLockCancel_${FP_LOCK_UID}:
    Abort "Install cancelled because FramePilot or framepilot-api is still running. Close the app and run the installer again. Do not Ignore locked-file errors."

  FramePilotLockDone_${FP_LOCK_UID}:
  !undef FP_LOCK_UID
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro FramePilotWaitForUnlockedTargets
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro FramePilotWaitForUnlockedTargets
!macroend
