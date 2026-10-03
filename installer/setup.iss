; Orbit Mouse Pro - Inno Setup Script
; Build with Inno Setup 6.x (https://jrsoftware.org/isdl.php)
; The release workflow passes the version from version.py:
;   ISCC.exe /DMyAppVersion=X.Y.Z installer\setup.iss
; Building by hand without /D falls back to the value below.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
; Same as Inno's implicit default (AppName) used by v1.1.0 and earlier,
; so upgrades replace the existing install instead of adding a second one
AppId=Orbit Mouse Pro
AppName=Orbit Mouse Pro
AppVersion={#MyAppVersion}
AppPublisher=Stellin-15
AppPublisherURL=https://stellin-15.github.io/Stress-Free/
AppSupportURL=https://github.com/Stellin-15/Stress-Free/issues
AppUpdatesURL=https://stellin-15.github.io/Stress-Free/
DefaultDirName={autopf}\Orbit Mouse Pro
DefaultGroupName=Orbit Mouse Pro
OutputDir=..\release
OutputBaseFilename=OrbitMousePro-Setup-v{#MyAppVersion}
SetupIconFile=..\Python Version\orbit.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Admin is for installing into Program Files. The app itself runs
; unelevated, and moving the mouse needs no special rights.
PrivilegesRequired=admin
; Minimum Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Start Orbit Mouse Pro when Windows starts"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Single-file exe produced by PyInstaller
Source: "..\Python Version\dist\OrbitMousePro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Orbit Mouse Pro"; Filename: "{app}\OrbitMousePro.exe"
Name: "{group}\Uninstall Orbit Mouse Pro"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Orbit Mouse Pro"; Filename: "{app}\OrbitMousePro.exe"; Tasks: desktopicon
Name: "{userstartup}\Orbit Mouse Pro"; Filename: "{app}\OrbitMousePro.exe"; Tasks: startupicon

[Run]
Filename: "{app}\OrbitMousePro.exe"; Description: "Launch Orbit Mouse Pro"; Flags: nowait postinstall skipifsilent

[Code]
// Remove startup shortcut on uninstall if it was created
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    DeleteFile(ExpandConstant('{userstartup}\Orbit Mouse Pro.lnk'));
end;
