; Orbit Mouse Pro - Inno Setup Script
; Build with Inno Setup 6.x (https://jrsoftware.org/isdl.php)
; Update AppVersion and OutputBaseFilename for every release.

[Setup]
AppName=Orbit Mouse Pro
AppVersion=1.1.0
AppPublisher=Stellin-15
AppPublisherURL=https://stellin-15.github.io/Stress-Free/
AppSupportURL=https://github.com/Stellin-15/Stress-Free/issues
AppUpdatesURL=https://stellin-15.github.io/Stress-Free/
DefaultDirName={autopf}\Orbit Mouse Pro
DefaultGroupName=Orbit Mouse Pro
OutputDir=..\release
OutputBaseFilename=OrbitMousePro-Setup-v1.1.0
SetupIconFile=..\Python Version\orbit.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Admin required so the app can move the mouse globally
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
