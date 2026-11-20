; Instalador de Invendesk con Inno Setup (https://jrsoftware.org/isinfo.php)
; 1) Ejecuta build.bat para generar dist\Invendesk.exe
; 2) Compila este archivo desde Inno Setup -> da installer\InvendeskSetup.exe

#define MyAppName "Invendesk"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Invendesk"
#define MyAppExeName "Invendesk.exe"

[Setup]
AppId={{8F1C4A1E-0E2B-4F7A-9C3D-5B9A0D2E1F40}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Invendesk
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=installer
OutputBaseFilename=InvendeskSetup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent