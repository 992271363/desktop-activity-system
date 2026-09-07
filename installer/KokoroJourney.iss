; ============================================================
; Kokoro Journey — Inno Setup 安装脚本
; 用法: ISCC.exe KokoroJourney.iss
; 前提: 先运行 build_release.ps1 生成 dist 目录
; ============================================================

#define MyAppName "Kokoro Journey"
#define MyAppVersion "2026.9.7-1.0.0"
#define MyAppPublisher "Kokoro Journey"
#define MyAppExeName "kokoro-journey.exe"
#define MyAppLogExeName "log-console.exe"
#define SourceDir "..\client\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Kokoro Journey
DefaultGroupName={#MyAppName}
OutputBaseFilename=KokoroJourneySetup-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "额外任务:"
Name: "autostart"; Description: "开机自动启动"; GroupDescription: "额外任务:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\client\.env"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesnotexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\日志控制台"; Filename: "{app}\{#MyAppLogExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "KokoroJourney"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
