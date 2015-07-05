; Script generated by the Inno Script Studio Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{DCEA27B3-F601-4340-93B3-63DA04613409}
AppName=Cloud-In-One
AppVersion=0.5
;AppVerName=Cloud-In-One 0.5
DefaultDirName={pf}\CLOUD_IN_ONE
DefaultGroupName=CLOUD_IN_ONE
OutputDir=dist
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\cloud-in-one.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\cio-crypt.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\sqlite3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\msvcr100.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\trusted-certs.crt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs  ; BeforeInstall: WriteAppPath
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Cloud-In-One"; Filename: "{app}\cloud-in-one.exe"
Name: "{group}\{cm:UninstallProgram,Cloud-In-One}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Cloud-In-One"; Filename: "{app}\cloud-in-one.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\cloud-in-one.exe"; Description: "{cm:LaunchProgram,Cloud-In-One}"; Flags: nowait postinstall skipifsilent;

[Code]
var
  DataDirPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  { Create the pages }

  DataDirPage := CreateInputDirPage(wpSelectDir,
    'Select Synchronization Directory', 'Where should your data be synced?',
    'Select the folder in which the Application should sync your files, then click Next.',
    False, '');
  DataDirPage.Add('');

  { Set default values, using settings that were stored last time if possible }

  DataDirPage.Values[0] := ExpandConstant('{userdocs}\CLOUD_IN_ONE');
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  S: String;
begin
  { Fill the 'Ready Memo' with the normal settings and the custom settings }
  S := 'Sync Folder: ' + DataDirPage.Values[0] + NewLine;

  Result := S;
end;

function GetDataDir(Param: String): String;
var
  S: String;
  S2: String;
begin
  { Return the selected DataDir }
  S := DataDirPage.Values[0];
  StringChangeEx(S, '\', '/', True);
  Result := S
end;

procedure WriteAppPath;
var
    FileData: String;
begin
    LoadStringFromFile(ExpandConstant('{app}\config\config.json'), FileData);
    StringChange(FileData, 'XXXXXMARKERXXXXX', GetDataDir(''));
    S := ExpandConstant('{userappdata}\CLOUD_IN_ONE');
    StringChangeEx(S, '\', '/', True);
    StringChange(FileData, 'XXXXXDATA_FOLDERXXXXX', S);
    SaveStringToFile(ExpandConstant('{app}\config\config.json'), FileData, False);
end;