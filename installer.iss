; BatchPix — Inno Setup Installer Script
; Compile with Inno Setup 6: https://jrsoftware.org/isinfo.php

#define MyAppName "BatchPix"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "E.P."
#define MyAppURL "https://github.com/erik-pinhasov/BatchPix"
#define MyAppExeName "BatchPix.exe"

[Setup]
AppId={{B4A7F3E2-8C1D-4F6A-9E2B-5D3C1A0F8E7B}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=installer_output
OutputBaseFilename=BatchPix_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "dist\BatchPix\BatchPix.exe"; DestDir: "{app}"; Flags: ignoreversion

; Internal dependencies (PyInstaller bundle)
Source: "dist\BatchPix\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Real-ESRGAN (AI enhancement engine)
Source: "dist\BatchPix\realesrgan\*"; DestDir: "{app}\realesrgan"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
