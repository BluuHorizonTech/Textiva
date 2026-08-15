; installer/textiva.iss
; Inno Setup 6+ script — produces Textiva-Setup-x.x.x.exe
; Docs: https://jrsoftware.org/ishelp/

#define MyAppName      "Textiva"
#define MyAppPublisher "BluuHorizonTech"
#define MyAppURL       "https://github.com/BluuHorizonTech/TypeFlow"
#define MyAppExeName   "Textiva.exe"
; Version is injected by the CI pipeline via /DMyAppVersion=x.x.x
; For local builds set it here:
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
; Basic identity
AppId={{6F4A2B1C-8D3E-4F5A-9B2C-1D4E5F6A7B8C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Output
OutputDir=output
OutputBaseFilename=Textiva-Setup-{#MyAppVersion}

; Install location
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Require admin so we can write to Program Files
PrivilegesRequired=admin

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Appearance
WizardStyle=modern
WizardResizable=no
DisableWelcomePage=no
SetupIconFile=

; Minimum Windows version: Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Desktop shortcut — unticked by default
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
      GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; Windows startup (silent background hook)
Name: "startup"; Description: "Start Textiva automatically when Windows starts"; \
      GroupDescription: "Startup:"; Flags: unchecked

[Files]
; The compiled exe from PyInstaller
; ".." resolves to the repo root since this file lives in installer/
Source: "..\dist\Textiva.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}";        Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall Textiva";   Filename: "{uninstallexe}"

; Desktop shortcut (only if task selected)
Name: "{autodesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; \
      Tasks: desktopicon

[Registry]
; Windows startup entry (only if task selected)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
      ValueType: string; ValueName: "{#MyAppName}"; \
      ValueData: """{app}\{#MyAppExeName}"" --no-gui"; \
      Flags: uninsdeletevalue; Tasks: startup

[Run]
; Offer to launch the app after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; \
          Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kill any running Textiva process before uninstall
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; \
          Flags: runhidden; RunOnceId: "KillTextiva"