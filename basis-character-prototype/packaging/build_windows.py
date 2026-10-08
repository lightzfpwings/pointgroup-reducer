"""Build the x64 Windows app on Windows; bundle .NET and an offline WebView2 installer."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = json.loads((ROOT / "package.json").read_text())["version"]
BUILD = ROOT / "build" / "windows-x64"
PACKAGE = BUILD / "BasisCharacter"
NATIVE = ROOT / "packaging" / "windows"

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

if sys.platform != "win32":
    raise SystemExit("This builder requires Windows x64 and the .NET 10 SDK.")
if os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() != "AMD64":
    raise SystemExit("Build on a native x64 Windows host.")
DIST.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)
run([sys.executable, str(ROOT / "build.py")])
if PACKAGE.exists():
    # 仅清理本脚本专用的构建目录，不触碰用户程序或历史发布包。
    if PACKAGE.parent != BUILD:
        raise SystemExit("Invalid build directory")
    shutil.rmtree(PACKAGE)
run(["dotnet", "publish", str(NATIVE / "BasisCharacter.csproj"), "-c", "Release", "-r", "win-x64",
     "--self-contained", "true", "-p:Version=" + VERSION, "-o", str(PACKAGE)])
resources = PACKAGE / "Resources"
resources.mkdir(exist_ok=True)
shutil.copy2(DIST / f"BasisCharacterPrototype-{VERSION}.html", resources / "index.html")
for name in ["engine.js", "reducer-catalog.js", "reducer-adapter.js", "reduction-catalog.js", "reduction-engine.js", "messages-data.js", "i18n.js", "math-format.js"]:
    shutil.copy2(ROOT / name, resources / name)
for language in ["zh-Hans", "zh-Hant", "en"]:
    offline = PACKAGE / "offline"
    offline.mkdir(exist_ok=True)
    path = DIST / f"BasisCharacterPrototype-{VERSION}-{language}.html"
    shutil.copy2(path, offline / path.name)
shutil.copytree(ROOT / "examples", PACKAGE / "examples")
for source, target in [("README.md", "使用说明.md"), ("README.en.md", "README-English.md"), ("README.zh-Hant.md", "使用說明.md")]:
    shutil.copy2(ROOT / source, PACKAGE / target)

# 随包保存 NuGet 自带许可证；不修改微软离线安装器。
licenses = PACKAGE / "licenses"
licenses.mkdir(exist_ok=True)
assets = json.loads((NATIVE / "obj" / "project.assets.json").read_text(encoding="utf-8"))
for library in assets["libraries"].values():
    if library.get("type") != "package":
        continue
    for folder in assets["packageFolders"]:
        source = Path(folder) / library["path"]
        if not source.exists():
            continue
        for path in source.rglob("*"):
            if path.is_file() and any(word in path.name.lower() for word in ("license", "thirdpartynotice", "copying")) and path.suffix.lower() in (".txt", ".md", "", ".html"):
                target = licenses / library["path"] / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)

installer = PACKAGE / "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
source_url = "https://go.microsoft.com/fwlink/p/?LinkId=2124701"
print("Downloading Microsoft's full offline WebView2 installer", flush=True)
with urllib.request.urlopen(source_url, timeout=120) as response, installer.open("wb") as destination:
    shutil.copyfileobj(response, destination)
runtime_report = BUILD / "webview2-installer-check.json"
# CI 的 PowerShell 7 模块路径不能传给 Windows PowerShell 5。
shell = shutil.which("pwsh") or "powershell"
shell_env = os.environ.copy()
if Path(shell).stem.lower() == "powershell":
    shell_env.pop("PSModulePath", None)
run([shell, "-NoProfile", "-NonInteractive", "-File", str(NATIVE / "verify-runtime.ps1"),
     "-Installer", str(installer), "-Report", str(runtime_report)], env=shell_env)
runtime = json.loads(runtime_report.read_text(encoding="utf-8-sig"))
check_path = BUILD / "native-self-check.json"
check_path.unlink(missing_ok=True)
run([str(PACKAGE / "BasisCharacter.exe"), "--self-check", str(check_path)], timeout=900)
report = json.loads(check_path.read_text(encoding="utf-8"))
report.update({"date": datetime.date.today().isoformat(), "architecture": "x64", "platform": "Windows",
               "dotnetBundled": True, "webview2OfflineInstaller": runtime, "appAuthenticodeSigned": False})
report_path = ROOT / "validation" / "windows-package-check.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
shutil.copy2(report_path, PACKAGE / report_path.name)
(PACKAGE / "START-HERE.txt").write_text(f"""点群与基函数 / 點群與基函數 / Point Groups & Basis Functions {VERSION}

Windows x64: Extract the ENTIRE ZIP, then open BasisCharacter.exe.
Windows 11 and Windows 10 x64 (1809 or later); supported Windows editions follow Microsoft's lifecycle.
No Python, Node.js or separate .NET installation is needed.
If asked for WebView2, run MicrosoftEdgeWebView2RuntimeInstallerX64.exe in this folder, then reopen the app.
The supplied Microsoft-signed installer works offline. It is not run automatically.

请完整解压 ZIP，再双击 BasisCharacter.exe。无需 Python、Node 或另装 .NET。
如提示缺少 WebView2，运行同文件夹中的微软离线安装器，再重新打开软件。
請完整解壓 ZIP，再雙擊 BasisCharacter.exe。無需 Python、Node 或另裝 .NET。
如提示缺少 WebView2，執行同資料夾中的微軟離線安裝器，再重新開啟軟體。

简体中文 / 繁體中文 / English: upper-right selector or native Language menu.
This executable is not Authenticode signed. UI rendering and native dialog interactions have not been visually automated.
""", encoding="utf-8")
archive = DIST / f"BasisCharacter-{VERSION}-Windows-x64.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
    for path in sorted(PACKAGE.rglob("*")):
        if path.is_file():
            output.write(path, "BasisCharacter/" + str(path.relative_to(PACKAGE)).replace("\\", "/"))
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(DIST / "WINDOWS-SHA256SUMS.txt").write_text(digest + "  " + archive.name + "\n", encoding="utf-8")
print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size, "sha256": digest, "selfCheck": "passed"}, indent=2))
