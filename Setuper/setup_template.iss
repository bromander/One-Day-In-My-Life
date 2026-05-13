#define MyAppName "OneDay"
#define MyAppVersion "1.0.5"
#define MyAppPublisher "piskisiski"
#define MyAppExeName "OneDaySetup.exe"
#define OtherFiles "C:\Program Files"
#define Repo "C:\Users\roma\PycharmProjects\JopaJam5SecretGame"

[Setup]
DisableWelcomePage=no
AppId={{FF1A8B07-3C43-463E-92FF-EC8CCF8BC449}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile={#Repo}\LICENSE_INFO.md
OutputDir="{#Repo}\Setuper\{#MyAppVersion}"
Compression=lzma
UsePreviousAppDir=no
SolidCompression=yes
DisableDirPage=no
WizardStyle=modern
OutputBaseFilename={#MyAppName}_{#MyAppVersion}_installer
SetupIconFile=pineapple.ico

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "{#Repo}\start.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Tasks]
Name: desktopicon; Description: "Создать ярлык на рабочем столе";

[Icons]
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\OneDay.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OneDay.exe"; Description: "Запустить {#MyAppName}"; Flags: postinstall nowait skipifsilent unchecked