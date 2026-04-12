; CPEDisateQ_installer.iss
; Script Inno Setup para CPE DisateQ™ v2.0.0
; Requiere que el .exe ya esté compilado por PyInstaller en dist\CPEDisateQ.exe

#define AppName "CPE DisateQ"
#define AppVersion "2.0.0"
#define AppPublisher "DisateQ"
#define AppURL "https://disateq.com"
#define AppExeName "CPEDisateQ.exe"
#define AppDescription "Motor de conversión y envío de facturación electrónica"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\DisateQ\CPE
DefaultGroupName=DisateQ\CPE DisateQ
AllowNoIcons=yes
LicenseFile=
OutputDir=D:\DATA\_Proyectos_\disateq\disateq-cpe-envio\installer_output
OutputBaseFilename=Setup_CPEDisateQ_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName} v{#AppVersion}
UninstallDisplayIcon={app}\{#AppExeName}
CreateUninstallRegKey=yes
PrivilegesRequired=admin
SetupIconFile=cpe_disateq.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "startupicon"; Description: "Iniciar CPE DisateQ al encender el equipo"; GroupDescription: "Inicio automático:"; Flags: unchecked

[Files]
Source: "D:\DATA\_Proyectos_\disateq\disateq-cpe-envio\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "D:\FFEESUNAT\CPE DisateQ"; Flags: uninsneveruninstall
Name: "D:\FFEESUNAT\CPE DisateQ\enviados"; Flags: uninsneveruninstall
Name: "D:\FFEESUNAT\CPE DisateQ\errores"; Flags: uninsneveruninstall
Name: "D:\FFEESUNAT\CPE DisateQ\status"; Flags: uninsneveruninstall
Name: "D:\FFEESUNAT\CPE DisateQ\rc"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Comment: "{#AppDescription}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Comment: "{#AppDescription}"; Tasks: desktopicon

[Registry]
; Inicio automático con Windows (opcional, solo si el usuario lo selecciona)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "CPEDisateQ"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--config"; Description: "Configurar {#AppName} ahora"; Flags: nowait postinstall

[UninstallRun]
Filename: "{app}\{#AppExeName}"; Parameters: "--exit"; Flags: skipifdoesntexist runhidden

[Messages]
WelcomeLabel1=Bienvenido al instalador de [name]
WelcomeLabel2=Este asistente instalará [name] v{#AppVersion} en su equipo.%n%nSe recomienda cerrar todas las aplicaciones antes de continuar.
FinishedLabel=La instalación de [name] ha concluido.%n%nHaga clic en Finalizar para cerrar este asistente.
