; Auto-launch application after installation
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchApp"

Function LaunchApp
  Exec "$INSTDIR\claude-proxy-installer.exe"
FunctionEnd