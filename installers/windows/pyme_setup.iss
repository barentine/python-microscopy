; PYME Windows Installer — produced by InnoSetup on windows-latest.
;
; This installer does NOT ship a pre-built venv. uv-managed venvs bake in an
; absolute path to their Python interpreter (see venv\pyvenv.cfg "home="
; and the Scripts\*.exe trampolines) — building the venv in CI and copying
; it into the installer leaves every launcher pointing at the CI runner's
; profile, which doesn't exist on the end user's machine ("uv trampoline
; failed to canonicalize script path"). Instead, this installer bundles
; install-python-microscopy.bat and runs it on the target machine, so the
; venv it creates is tied to that machine from the start.
;
; Typical CI invocation (from a checkout of the repo, no bundle build needed):
;   set VERSION=<version string for this release>
;   ISCC.exe /DRepoDir=C:\path\to\checkout /DAppVersion=%VERSION% pyme_setup.iss

#ifndef RepoDir
  #define RepoDir "..\.."
#endif
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName      "PYME"
#define AppPublisher "Baddeley Lab, University of Auckland"
; Icons are staged from the source tree (not the venv) so they're available
; before install-python-microscopy.bat has run.
; pymeLogo.png has no .ico equivalent — pmanal.ico is used in its place.
#define IconsDir     "{#RepoDir}\PYME\resources\icons"

[Setup]
; AppId uniquely identifies this application for upgrades and uninstall — do not change.
AppId={{8F3A2E1D-6B4C-4D9F-A7E2-3C1B5F8A2D6E}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
; Per-user install by default; elevation dialog allows all-users install.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=PYME-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Avoid prompting to close running apps — PYME processes are independent.
CloseApplications=no

[Files]
Source: "{#RepoDir}\installers\install-python-microscopy.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#IconsDir}\pmacquire.ico"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "{#IconsDir}\pmanal.ico";    DestDir: "{app}\icons"; Flags: ignoreversion
Source: "{#IconsDir}\pmvis.ico";     DestDir: "{app}\icons"; Flags: ignoreversion

[Run]
; Runs on the target machine so uv, the managed Python, and the venv it
; creates are all tied to this machine — not skippable in silent installs,
; since the app is non-functional without it.
Filename: "{cmd}"; Parameters: "/C ""{app}\install-python-microscopy.bat"" ""{app}"""; \
    WorkingDir: "{app}"; StatusMsg: "Installing Python and PYME (requires internet access; this can take several minutes)..."; \
    Flags: waituntilterminated

[Icons]
Name: "{group}\PYMEAcquire";      Filename: "{app}\PYMEAcquire.cmd";      IconFilename: "{app}\icons\pmacquire.ico"
Name: "{group}\PYMEImage";        Filename: "{app}\PYMEImage.cmd";        IconFilename: "{app}\icons\pmanal.ico"
Name: "{group}\PYMEVis";          Filename: "{app}\PYMEVis.cmd";          IconFilename: "{app}\icons\pmvis.ico"
Name: "{group}\PYMEClusterOfOne"; Filename: "{app}\PYMEClusterOfOne.cmd"; IconFilename: "{app}\icons\pmanal.ico"
Name: "{group}\PYME Console";     Filename: "{app}\pyme-console.cmd";     IconFilename: "{app}\icons\pmanal.ico"
Name: "{group}\Uninstall PYME";   Filename: "{uninstallexe}"
