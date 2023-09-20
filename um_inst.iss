[Setup]
AppName=Unique Matcher
AppVersion=0.3.0
DefaultDirName=UniqueMatcher
OutputBaseFilename=UniqueMatcherInstall
SetupIconFile=um.ico

[Files]
Source: "assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs
Source: "dist\UniqueMatcher\*"; DestDir: "{app}"; Flags: recursesubdirs
Source: "Tesseract-OCR\*"; DestDir: "{app}\Tesseract-OCR"; Flags: recursesubdirs

Source: "config.ini"; DestDir: "{app}"; Flags: onlyifdoesntexist
Source: "screen.exe"; DestDir: "{app}"
Source: "items.csv"; DestDir: "{app}"
Source: "README.md"; DestDir: "{app}"
Source: "LICENSE"; DestDir: "{app}"

[Dirs]
Name: "{app}\data"
Name: "{app}\data\logs"
Name: "{app}\data\queue"
Name: "{app}\data\done"
Name: "{app}\data\errors"
