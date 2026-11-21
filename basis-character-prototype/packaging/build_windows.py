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
APPLICATION_BINARIES = ("BasisCharacter.exe", "BasisCharacter.dll")


def powershell():
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        raise SystemExit("PowerShell is required for Windows signature verification.")
    env = os.environ.copy()
    if Path(shell).stem.lower() == "powershell":
        env.pop("PSModulePath", None)
    return shell, env


def find_signtool():
    configured = os.environ.get("SIGNTOOL_PATH")
    if configured:
        if not Path(configured).is_file():
            raise SystemExit("SIGNTOOL_PATH does not identify an installed SignTool executable.")
        return configured
    found = shutil.which("signtool")
    if found:
        return found
    sdk = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    candidates = list(sdk.glob("*/x64/signtool.exe"))
    if candidates:
        def version(path):
            return tuple(int(part) if part.isdigit() else 0 for part in path.parents[1].name.split("."))
        return str(max(candidates, key=version))
    raise SystemExit("Install Windows SDK SignTool or set SIGNTOOL_PATH before signing/verification.")


def authenticate_application(package, args):
    required = bool(args.require_signature or args.sign_thumbprint or args.expected_signer_subject)
    if not required:
        return {"status": "not-requested", "mode": "development", "files": []}
    report_path = BUILD / "authenticode-check.json"
    report_path.unlink(missing_ok=True)
    shell, env = powershell()
    command = [shell, "-NoProfile", "-NonInteractive", "-File", str(NATIVE / "sign-app.ps1"),
               "-Package", str(package), "-Report", str(report_path), "-SignTool", find_signtool()]
    if args.sign_thumbprint:
        command.extend(["-Thumbprint", args.sign_thumbprint, "-TimestampUrl", args.sign_timestamp_url])
    if args.sign_machine_store:
        command.append("-MachineStore")
    if args.expected_signer_subject:
        command.extend(["-ExpectedSignerSubject", args.expected_signer_subject])
    subprocess.run(command, check=True, timeout=900, env=env)
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    if (report.get("status") != "passed" or len(report["files"]) != len(APPLICATION_BINARIES)
            or {entry["path"] for entry in report["files"]} != set(APPLICATION_BINARIES)):
        raise SystemExit("Incomplete application signature verification report.")
    for entry in report["files"]:
        binary = package / entry["path"]
        if not all(entry.get(field) for field in ("sha256", "subject", "thumbprint", "timestampSubject", "timestampThumbprint")):
            raise SystemExit("Incomplete publisher or timestamp information in signature report.")
        if sha256(binary) != entry["sha256"]:
            raise SystemExit("Application binary changed after signature verification.")
    return report


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
        ("README.zh-Hant.md", "使用說明.md"), ("SIGNING.md", "SIGNING.md"),
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
    shell, env = powershell()
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
    inventory = package / "basis-package-files.json"
    managed = {path.relative_to(package).as_posix(): sha256(path) for path in sorted(package.rglob("*"))
               if path.is_file() and path != inventory}
    inventory.write_text(json.dumps(managed, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    suffix = "" if full else "-lite"
    archive = DIST / f"BasisCharacter-{VERSION}-Windows-x64{suffix}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                compression = zipfile.ZIP_STORED if path.name == WEBVIEW2_INSTALLER else zipfile.ZIP_DEFLATED
                output.write(path, f"BasisCharacter/{path.relative_to(package).as_posix()}", compress_type=compression)
    return archive


def prepare_lite_resources(package, bundle):
    # A second --package-only run may start from the previous full-package tree.
    # Reset only generated offline resources; preserve all signed binaries.
    offline = package / "offline"
    offline.mkdir(exist_ok=True)
    for language in ("zh-Hans", "zh-Hant", "en"):
        (offline / f"{bundle.stem}-{language}.html").unlink(missing_ok=True)
    shutil.copy2(bundle, offline / bundle.name)
    (package / WEBVIEW2_INSTALLER).unlink(missing_ok=True)
    write_start_here(package, full=False)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-full", action="store_true", help="Also build the ZIP with the signed offline WebView2 installer.")
    phase = parser.add_mutually_exclusive_group()
    phase.add_argument("--build-only", action="store_true", help="Build and self-check, then leave binaries ready for an external signing service.")
    phase.add_argument("--package-only", action="store_true", help="Verify and package the existing build without compiling or overwriting signatures.")
    parser.add_argument("--require-signature", action="store_true", help="Require trusted, timestamped Authenticode signatures before packaging.")
    parser.add_argument("--expected-signer-subject", help="Exact publisher certificate Subject; also requires signature verification.")
    parser.add_argument("--sign-thumbprint", help="Sign with this 40-hex certificate from My store, then verify; keys remain in their provider.")
    parser.add_argument("--sign-machine-store", action="store_true", help="Use LocalMachine rather than CurrentUser My certificate store.")
    parser.add_argument("--sign-timestamp-url", default="http://timestamp.digicert.com", help="RFC3161 service for certificate-store signing.")
    args = parser.parse_args(argv)
    if args.require_signature and not (args.expected_signer_subject or args.sign_thumbprint):
        parser.error("--require-signature needs --expected-signer-subject or --sign-thumbprint to pin the publisher")
    if args.sign_machine_store and not args.sign_thumbprint:
        parser.error("--sign-machine-store needs --sign-thumbprint")
    if args.sign_thumbprint and (len(args.sign_thumbprint) != 40 or any(c not in "0123456789abcdefABCDEF" for c in args.sign_thumbprint)):
        parser.error("--sign-thumbprint must contain exactly 40 hexadecimal characters")
    return args


def main():
    args = parse_args()
    if sys.platform != "win32" or os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() != "AMD64":
        raise SystemExit("Build on native Windows x64 with the .NET 10 SDK.")
    package = BUILD / "BasisCharacter"
    DIST.mkdir(exist_ok=True)
    report_path = DIST / "windows-package-check.json"
    # A failed build/verification must not leave an old archive looking releasable.
    report_path.unlink(missing_ok=True)
    (DIST / "WINDOWS-SHA256SUMS.txt").unlink(missing_ok=True)
    for suffix in ("", "-lite"):
        (DIST / f"BasisCharacter-{VERSION}-Windows-x64{suffix}.zip").unlink(missing_ok=True)
    if args.package_only:
        bundle = DIST / f"BasisCharacterPrototype-{VERSION}.html"
        if not bundle.is_file() or not all((package / name).is_file() for name in APPLICATION_BINARIES):
            raise SystemExit("Run --build-only before --package-only, in the same build workspace.")
    else:
        bundle = build_html()
        if package.exists():
            shutil.rmtree(package)
        subprocess.run(
            ["dotnet", "publish", str(NATIVE / "BasisCharacter.csproj"), "-c", "Release",
             "-r", "win-x64", "--self-contained", "true", f"-p:Version={VERSION}", "-o", str(package)],
            check=True,
        )
        stage_distribution(package, bundle)
        copy_licenses(package)
    authenticity = authenticate_application(package, args)
    check_path = BUILD / "native-self-check.json"
    check_path.unlink(missing_ok=True)
    subprocess.run([str(package / "BasisCharacter.exe"), "--self-check", str(check_path)], check=True, timeout=900)
    report = json.loads(check_path.read_text(encoding="utf-8"))
    if report.get("status") != "passed" or report.get("version") != VERSION:
        raise SystemExit("Calculation self-check failed or belongs to another application version.")
    report.update({"date": datetime.date.today().isoformat(), "architecture": "x64", "platform": "Windows",
                   "dotnetBundled": True, "webview2OfflineInstaller": "separate download",
                   "appAuthenticodeSigned": authenticity["status"] == "passed", "appAuthenticode": authenticity})
    # The headless check must not change any binary after the trust check.
    for entry in authenticity["files"]:
        if sha256(package / entry["path"]) != entry["sha256"]:
            raise SystemExit("Application binary changed during the calculation self-check.")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(report_path, package / report_path.name)
    if args.build_only:
        print(json.dumps({"build": str(package), "selfCheck": "passed", "packaged": False}, indent=2))
        return
    prepare_lite_resources(package, bundle)
    archives = [archive_distribution(package)]
    if args.with_full:
        report["webview2OfflineInstaller"] = install_full_resources(package, bundle)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(report_path, package / report_path.name)
        archives.append(archive_distribution(package, full=True))
    results = [{"archive": archive.name, "bytes": archive.stat().st_size, "sha256": sha256(archive)} for archive in archives]
    (DIST / "WINDOWS-SHA256SUMS.txt").write_text(
        "".join(f"{result['sha256']}  {result['archive']}\n" for result in results), encoding="utf-8"
    )
    print(json.dumps({"packages": results, "selfCheck": "passed"}, indent=2))


if __name__ == "__main__":
    main()
