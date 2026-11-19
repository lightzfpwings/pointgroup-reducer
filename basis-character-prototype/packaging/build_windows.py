"""Build the x64 Windows app with a bundled .NET runtime."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import CORE_SCRIPTS, DIST, VERSION, build_html, language_pages, sha256

BUILD = ROOT / "build" / "windows-x64"
NATIVE = ROOT / "packaging" / "windows"
WEBVIEW2_URL = "https://developer.microsoft.com/microsoft-edge/webview2/#download"
WEBVIEW2_INSTALLER = "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
WEBVIEW2_OFFLINE_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124701"


def stage_distribution(package, bundle):
    resources = package / "Resources"
    resources.mkdir(exist_ok=True)
    shutil.copy2(bundle, resources / "index.html")
    # The executable's headless self-check loads the modules individually.
    for name in CORE_SCRIPTS:
        shutil.copy2(ROOT / name, resources / name)

    offline = package / "offline"
    offline.mkdir(exist_ok=True)
    shutil.copy2(bundle, offline / bundle.name)
    shutil.copytree(ROOT / "examples", package / "examples", dirs_exist_ok=True)
    for source, target in (
        ("README.md", "使用说明.md"), ("README.en.md", "README-English.md"),
        ("README.zh-Hant.md", "使用說明.md"),
    ):
        shutil.copy2(ROOT / source, package / target)
    (package / "Download-WebView2.url").write_bytes(
        f"[InternetShortcut]\r\nURL={WEBVIEW2_URL}\r\n".encode("ascii")
    )
    write_start_here(package, full=False)


def write_start_here(package, *, full):
    if full:
        english = f"If WebView2 is missing, run {WEBVIEW2_INSTALLER} from this folder, then reopen the app."
        simplified = f"若提示缺少 WebView2，运行本目录的 {WEBVIEW2_INSTALLER}，安装后重开应用。"
        traditional = f"若提示缺少 WebView2，執行此資料夾的 {WEBVIEW2_INSTALLER}，安裝後重新開啟應用程式。"
    else:
        english = """If WebView2 is missing, open Download-WebView2.url and choose Evergreen Standalone
Installer (x64). Install it, then reopen the app. For an offline PC, download it on another PC."""
        simplified = "若提示缺少 WebView2，打开 Download-WebView2.url，下载 Evergreen 独立安装程序 x64。安装后重开应用。"
        traditional = "若提示缺少 WebView2，開啟 Download-WebView2.url，下載 Evergreen 獨立安裝程式 x64。安裝後重新開啟應用程式。"
    (package / "START-HERE.txt").write_text(f"""点群与基函数 / 點群與基函數 / Point Groups & Basis Functions {VERSION}

Windows x64: Extract the entire ZIP and open BasisCharacter.exe. .NET is included.
{english}
The offline folder contains HTML you can open and switch between all three languages.

请完整解压 ZIP 后打开 BasisCharacter.exe。已包含 .NET。
{simplified}
offline 文件夹里的 HTML 可离线打开并切换三语。

請完整解壓 ZIP 後開啟 BasisCharacter.exe。已包含 .NET。
{traditional}
offline 資料夾內的 HTML 可離線開啟並切換三語。
""", encoding="utf-8")


def install_full_resources(package, bundle):
    installer = package / WEBVIEW2_INSTALLER
    with urllib.request.urlopen(WEBVIEW2_OFFLINE_URL, timeout=120) as response, installer.open("wb") as destination:
        shutil.copyfileobj(response, destination)
    report = BUILD / "webview2-installer-check.json"
    shell = shutil.which("pwsh") or "powershell"
    env = os.environ.copy()
    if Path(shell).stem.lower() == "powershell":
        env.pop("PSModulePath", None)
    subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File", str(NATIVE / "verify-runtime.ps1"),
                    "-Installer", str(installer), "-Report", str(report)], check=True, env=env)

    offline = package / "offline"
    (offline / bundle.name).unlink()
    for page in language_pages(bundle.read_text(encoding="utf-8")):
        shutil.copy2(page, offline / page.name)
    write_start_here(package, full=True)
    return json.loads(report.read_text(encoding="utf-8-sig"))


def copy_licenses(package):
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
                    target = package / "licenses" / library["path"] / path.relative_to(source)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)


def archive_distribution(package, *, full=False):
    suffix = "" if full else "-lite"
    archive = DIST / f"BasisCharacter-{VERSION}-Windows-x64{suffix}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                compression = zipfile.ZIP_STORED if path.name == WEBVIEW2_INSTALLER else zipfile.ZIP_DEFLATED
                output.write(path, f"BasisCharacter/{path.relative_to(package).as_posix()}", compress_type=compression)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-full", action="store_true", help="Also build the ZIP with the signed offline WebView2 installer.")
    args = parser.parse_args()
    if sys.platform != "win32" or os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() != "AMD64":
        raise SystemExit("Build on native Windows x64 with the .NET 10 SDK.")
    bundle = build_html()
    package = BUILD / "BasisCharacter"
    if package.exists():
        shutil.rmtree(package)
    subprocess.run(
        ["dotnet", "publish", str(NATIVE / "BasisCharacter.csproj"), "-c", "Release",
         "-r", "win-x64", "--self-contained", "true", f"-p:Version={VERSION}", "-o", str(package)],
        check=True,
    )
    stage_distribution(package, bundle)
    copy_licenses(package)
    check_path = BUILD / "native-self-check.json"
    check_path.unlink(missing_ok=True)
    subprocess.run([str(package / "BasisCharacter.exe"), "--self-check", str(check_path)], check=True, timeout=900)
    report = json.loads(check_path.read_text(encoding="utf-8"))
    report.update({"date": datetime.date.today().isoformat(), "architecture": "x64", "platform": "Windows",
                   "dotnetBundled": True, "webview2OfflineInstaller": "separate download", "appAuthenticodeSigned": False})
    report_path = DIST / "windows-package-check.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(report_path, package / report_path.name)
    archives = [archive_distribution(package)]
    if args.with_full:
        report["webview2OfflineInstaller"] = install_full_resources(package, bundle)
        (package / report_path.name).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        archives.append(archive_distribution(package, full=True))
    results = [{"archive": archive.name, "bytes": archive.stat().st_size, "sha256": sha256(archive)} for archive in archives]
    (DIST / "WINDOWS-SHA256SUMS.txt").write_text(
        "".join(f"{result['sha256']}  {result['archive']}\n" for result in results), encoding="utf-8"
    )
    print(json.dumps({"packages": results, "selfCheck": "passed"}, indent=2))


if __name__ == "__main__":
    main()
