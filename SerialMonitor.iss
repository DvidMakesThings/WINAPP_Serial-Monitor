; ---------------------------------------------------------------------------
; SerialMonitor.iss
; Inno Setup script for a --onefile PyInstaller bundle
; ---------------------------------------------------------------------------

[Setup]
; Installer UI
AppName=Serial Monitor
AppVersion=1.0
DefaultDirName={pf}\SerialMonitor
DisableProgramGroupPage=yes
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
; Change this to whatever you want your installer called:
OutputBaseFilename=SerialMonitor Installer

[Files]
; Package your single-file EXE
Source: "dist\Serial Monitor.exe"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Make sure your app has a writable spot for commands.xml
Name: "{commonappdata}\SerialMonitor"

[Icons]
; Start menu & optional desktop shortcut
Name: "{group}\Serial Monitor"; Filename: "{app}\Serial Monitor.exe"
Name: "{commondesktop}\Serial Monitor"; Filename: "{app}\Serial Monitor.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; Flags: unchecked

[Run]
; Offer to launch on finish
Filename: "{app}\Serial Monitor.exe"; Description: "Launch Serial Monitor"; Flags: nowait postinstall skipifsilent
