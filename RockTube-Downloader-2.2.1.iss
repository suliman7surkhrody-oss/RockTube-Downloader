#define MyAppName "RockTube Downloader"
#define MyAppVersion "2.2.1"
#define MyAppPublisher "Mr.Sulim.Inc"
#define MyAppExeName "RockTube Downloader.exe"

[Setup]
AppId={{8D3B7E91-5A22-4E88-B8E9-ROCKTUBE220}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\RockTube Downloader
DefaultGroupName={#MyAppName}

OutputDir=InstallerOutput-2.2.1
OutputBaseFilename=RockTube-Downloader-Setup-2.2.1

SetupIconFile=rocktube.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

WizardStyle=modern
Compression=lzma2
SolidCompression=yes

DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no

VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Windows Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Files]
Source: "build-output-2.2.1\RockTube Downloader\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{commondesktop}\RockTube Downloader"; Filename: "{app}\RockTube Downloader.exe"; WorkingDir: "{app}"
Name: "{group}\RockTube Downloader"; Filename: "{app}\RockTube Downloader.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall RockTube Downloader"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\RockTube Downloader.exe"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent