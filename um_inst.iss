[Setup]
AppName=Unique Matcher
AppVersion=0.2.0
DefaultDirName=UniqueMatcher
OutputBaseFilename=UniqueMatcherInstall

[Files]
Source: "items\*"; DestDir: "{app}\items"
Source: "socket\*"; DestDir: "{app}\socket"
Source: "templates\*"; DestDir: "{app}\templates"
Source: "dist\UniqueMatcher\*"; DestDir: "{app}"; Flags: recursesubdirs
Source: "unique_matcher\gui\qml\*"; DestDir: "{app}\unique_matcher\gui\qml"

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
