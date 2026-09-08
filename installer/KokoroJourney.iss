; ============================================================
; Kokoro Journey — Inno Setup 安装脚本
; 用法: ISCC.exe KokoroJourney.iss
;       或注入版本号: ISCC.exe /DMyAppVersion="v2026.9.7-1.0.0" KokoroJourney.iss
; 前提: 先运行 build_release.ps1 生成 dist 目录
; ============================================================

#define MyAppName "Kokoro Journey"
#ifndef MyAppVersion
#define MyAppVersion "v2026.9.7-1.0.0"
#endif
#define MyAppPublisher "Kokoro Journey"
#define MyAppExeName "kokoro-journey.exe"
#define MyAppLogExeName "log-console.exe"
#define SourceDir "..\client\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppId={{B7F3A2C1-8D4E-4F6A-9C2B-1E5D7A8F3E90}
DefaultDirName={localappdata}\Programs\Kokoro Journey
DefaultGroupName={#MyAppName}
OutputDir=..\installer_output
OutputBaseFilename=KokoroJourneySetup-{#MyAppVersion}
SetupIconFile=..\client\icons\icon.ico
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
Source: "..\client\.env.example"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesnotexist
Source: "uninstall_data_handler.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: {app}
Name: "{group}\日志控制台"; Filename: "{app}\{#MyAppLogExeName}"; WorkingDir: {app}
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: {app}; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "KokoroJourney"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: powershell.exe; Parameters: "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""{app}\uninstall_data_handler.ps1"" ""{localappdata}\Kokoro Journey\uninstall_state.json""; Flags: runasoriginaluser waituntilterminated
