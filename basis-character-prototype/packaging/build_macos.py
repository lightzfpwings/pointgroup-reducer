"""Build a standalone arm64 macOS app with system AppKit/WebKit."""
import argparse
from pathlib import Path
import datetime
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import UUID
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import DIST, VERSION, build_html, language_pages, sha256

BUILD = ROOT / "build" / "macos-arm64"
APP = DIST / "BasisCharacter.app"
BUNDLE_ID = "org.symmetrygroup.basischaracter.prototype"
DEVELOPER_ID = ("anchor apple generic and certificate 1[field.1.2.840.113635.100.6.2.6] "
                "and certificate leaf[field.1.2.840.113635.100.6.1.13]")


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def verify_signature(app, *, distribution=False):
    requirement = ["-R=" + DEVELOPER_ID] if distribution else []
    run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", *requirement, str(app)])


def archive_bundle(app, destination):
    # Archive a containing directory so ditto preserves metadata on the app directory itself.
    with TemporaryDirectory(dir=BUILD, prefix="bundle-") as temporary:
        run(["/usr/bin/ditto", str(app), str(Path(temporary) / app.name)])
        run(["/usr/bin/ditto", "-c", "-k", "--rsrc", "--extattr", "--sequesterRsrc",
             temporary, str(destination)])


def notarize(archive, target, profile, keychain):
    credentials = ["--keychain-profile", profile]
    if keychain:
        credentials.extend(["--keychain", keychain])
    print(f"Waiting for Apple notarization of {archive.name}.", flush=True)
    submission = subprocess.run(["xcrun", "notarytool", "submit", str(archive), *credentials,
                                 "--wait", "--timeout", "45m", "--output-format", "json"],
                                stdout=subprocess.PIPE, text=True)
    try:
        details = json.loads(submission.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit("Apple notarytool did not return a notarization result.") from error
    submission_id = str(UUID(details["id"]))
    print(f"Apple notarization {submission_id}: {details['status']}", flush=True)
    if details["status"] == "In Progress":
        raise SystemExit("Apple has not completed this submission within the build's wait limit.")
    log = run(["xcrun", "notarytool", "log", submission_id, *credentials],
              stdout=subprocess.PIPE, text=True)
    (BUILD / f"notarization-{archive.suffix[1:]}-log.json").write_text(log.stdout, encoding="utf-8")
    for issue in json.loads(log.stdout).get("issues") or []:
        print(f"Apple notarization {issue['severity']}: {issue['path']}: {issue['message']}", file=sys.stderr)
    if submission.returncode != 0 or details["status"] != "Accepted":
        raise SystemExit("Apple did not accept notarization. See the notarization log in the build directory.")
    run(["xcrun", "stapler", "staple", str(target)])
    run(["xcrun", "stapler", "validate", str(target)])
    return submission_id


def verify_packaged_app(app, executable_hash, *, distribution=False):
    verify_signature(app, distribution=distribution)
    if sha256(app / "Contents" / "MacOS" / "BasisCharacter") != executable_hash:
        raise SystemExit("Packaged executable differs from the checked app.")
    if distribution:
        run(["xcrun", "stapler", "validate", str(app)])
        if Path("/usr/bin/syspolicy_check").is_file():
            run(["/usr/bin/syspolicy_check", "distribution", str(app)])
        else:
            run(["/usr/sbin/spctl", "--assess", "--type", "execute", "--verbose=2", str(app)])


def verify_archive(archive, executable_hash, *, distribution=False):
    with zipfile.ZipFile(archive) as packaged:
        if packaged.testzip() is not None:
            raise SystemExit(f"ZIP integrity check failed: {archive.name}")
    with TemporaryDirectory(dir=BUILD, prefix="verify-") as temporary:
        run(["/usr/bin/ditto", "-x", "-k", str(archive), temporary])
        verify_packaged_app(Path(temporary) / APP.name, executable_hash, distribution=distribution)


def build_disk_image(destination, app_report, identity, profile, keychain):
    image = destination / f"BasisCharacter-{VERSION}-macOS-arm64.dmg"
    with TemporaryDirectory(dir=BUILD, prefix="dmg-contents-") as temporary:
        contents = Path(temporary)
        run(["/usr/bin/ditto", str(APP), str(contents / APP.name)])
        (contents / "Applications").symlink_to("/Applications", target_is_directory=True)
        run(["/usr/bin/hdiutil", "create", "-srcfolder", temporary, "-volname", "BasisCharacter",
             "-fs", "HFS+", "-mode", "0755", "-format", "UDZO", str(image)])

    distribution = app_report["notarized"]
    signing = {"signature": "unsigned disk image", "notarized": False, "stapled": False,
               "gatekeeper": "not checked"}
    if distribution:
        keychain_flags = ["--keychain", keychain] if keychain else []
        run(["codesign", "--sign", identity, *keychain_flags, "--timestamp",
             "--identifier", BUNDLE_ID + ".dmg", str(image)])
        team = app_report["teamIdentifier"]
        requirements = f'{DEVELOPER_ID} and certificate leaf[subject.OU] = "{team}"'
        submission_id = notarize(image, image, profile, keychain)
        run(["codesign", "--verify", "--strict", "--verbose=2", "-R=" + requirements, str(image)])
        run(["/usr/sbin/spctl", "--assess", "--type", "open", "--context", "context:primary-signature",
             "--verbose=2", str(image)])
        signing.update(signature="Developer ID Application", teamIdentifier=team, notarized=True,
                       notarizationId=submission_id, appNotarizationId=app_report["notarizationId"],
                       stapled=True, gatekeeper="passed")

    run(["/usr/bin/hdiutil", "verify", str(image)])
    executable_hash = app_report["appExecutableSha256"]
    with TemporaryDirectory(dir=BUILD, prefix="dmg-mount-") as mount:
        run(["/usr/bin/hdiutil", "attach", str(image), "-readonly", "-nobrowse", "-mountpoint", mount])
        try:
            applications = Path(mount) / "Applications"
            if not applications.is_symlink() or os.readlink(applications) != "/Applications":
                raise SystemExit("The disk image does not contain the expected Applications shortcut.")
            mounted_app = Path(mount) / APP.name
            verify_packaged_app(mounted_app, executable_hash, distribution=distribution)
            if sha256(mounted_app / "Contents/Resources/index.html") != app_report["offlineHTMLSha256"]:
                raise SystemExit("The mounted app contains a different offline page.")
            check = subprocess.check_output([str(mounted_app / "Contents/MacOS/BasisCharacter"),
                                             "--self-check"], text=True, timeout=120)
            mounted_report = json.loads(check)
            if (mounted_report.get("version") != VERSION or mounted_report.get("status") != "passed"
                    or mounted_report.get("waterSalcChecks") != app_report["waterSalcChecks"]):
                raise SystemExit("The mounted app failed its calculation self-check.")
        finally:
            run(["/usr/bin/hdiutil", "detach", mount])

    return image, {"status": "passed", "version": VERSION, "architecture": "arm64",
                   "minimumMacOS": app_report["minimumMacOS"], "imageSha256": sha256(image),
                   "appExecutableSha256": executable_hash, "offlineHTMLSha256": app_report["offlineHTMLSha256"],
                   "mountedSelfCheck": "passed", **signing}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--with-full", action="store_true", help="Also build the ZIP with three language-specific offline pages.")
parser.add_argument("--with-dmg", action="store_true", help="Also build a drag-to-Applications disk image.")
parser.add_argument("--sign-and-notarize", action="store_true", help="Use a Developer ID Application identity and an Apple notarization profile.")
args = parser.parse_args()
if sys.platform != "darwin":
    raise SystemExit("This builder requires macOS and Apple's command line tools.")
identity = "-"
keychain = ""
profile = ""
if args.sign_and_notarize:
    identity = os.getenv("MACOS_SIGNING_IDENTITY", "").strip()
    profile = os.getenv("MACOS_NOTARY_PROFILE", "").strip()
    keychain = os.getenv("MACOS_SIGNING_KEYCHAIN", "")
    if not identity or identity == "-" or not profile:
        parser.error("--sign-and-notarize requires MACOS_SIGNING_IDENTITY and MACOS_NOTARY_PROFILE")
    if keychain and not Path(keychain).is_file():
        parser.error("MACOS_SIGNING_KEYCHAIN must point to an existing keychain file")
BUILD.mkdir(parents=True, exist_ok=True)
bundle = build_html()
if APP.exists():
    info = plistlib.loads((APP / "Contents" / "Info.plist").read_bytes())
    if info.get("CFBundleIdentifier") != BUNDLE_ID:
        raise SystemExit("Refusing to replace a different application.")
    shutil.rmtree(APP)
macos = APP / "Contents" / "MacOS"
resources = APP / "Contents" / "Resources"
macos.mkdir(parents=True)
resources.mkdir()
shutil.copy2(bundle, resources / "index.html")
shutil.copy2(ROOT / "packaging" / "self-check.js", resources)
shutil.copy2(ROOT / "packaging" / "icons" / "basis-character.icns", resources)
for language, display in {"zh-Hans":"点群与基函数","zh-Hant":"點群與基函數","en":"Point Groups & Basis Functions"}.items():
    folder=resources/(language+".lproj");folder.mkdir()
    (folder/"InfoPlist.strings").write_text('"CFBundleDisplayName" = '+json.dumps(display,ensure_ascii=False)+';\n',encoding='utf-8')
info = {
    "CFBundleName": "BasisCharacter", "CFBundleDisplayName": "点群与基函数",
    "CFBundleIdentifier": BUNDLE_ID,
    "CFBundleIconFile": "basis-character.icns",
    "CFBundleExecutable": "BasisCharacter", "CFBundlePackageType": "APPL",
    "CFBundleShortVersionString": VERSION, "CFBundleVersion": "13",
    "CFBundleLocalizations": ["zh-Hans", "zh-Hant", "en"], "CFBundleDevelopmentRegion": "en",
    "LSMinimumSystemVersion": "12.0", "NSHighResolutionCapable": True,
    "NSHumanReadableCopyright": "Integrated basis characters and irreducible reduction.",
    "NSPrincipalClass": "NSApplication",
}
(APP / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info))
sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
env = os.environ.copy()
env["CLANG_MODULE_CACHE_PATH"] = str(BUILD / "module-cache")
run(["xcrun", "swiftc", str(ROOT / "packaging" / "macos" / "main.swift"),
     "-swift-version", "5", "-parse-as-library", "-target", "arm64-apple-macos12.0", "-sdk", sdk,
     "-module-cache-path", str(BUILD / "module-cache"), "-O",
     "-framework", "Cocoa", "-framework", "WebKit", "-framework", "JavaScriptCore",
     "-o", str(macos / "BasisCharacter")], env=env)
sign_flags = ["--keychain", keychain] if keychain else []
sign_flags += ["--options", "runtime", "--timestamp"] if args.sign_and_notarize else ["--timestamp=none"]
run(["codesign", "--force", "--sign", identity, *sign_flags, str(APP)])
verify_signature(APP, distribution=args.sign_and_notarize)
check = subprocess.check_output([str(macos / "BasisCharacter"), "--self-check"], text=True)
report = json.loads(check)
report.update({"date": datetime.date.today().isoformat(), "architecture": "arm64", "minimumMacOS": "12.0",
               "signature": "ad-hoc local signature", "notarized": False, "stapled": False,
               "gatekeeper": "not checked", "appExecutableSha256": sha256(macos / "BasisCharacter"),
               "offlineHTMLSha256": sha256(bundle)})
signing_note = "此包使用本地临时签名，尚未经过 Apple 开发者签名和公证。"
if args.sign_and_notarize:
    signing = run(["codesign", "--display", "--verbose=4", str(APP)], stderr=subprocess.PIPE, text=True)
    team = next((line.split("=", 1)[1] for line in signing.stderr.splitlines()
                 if line.startswith("TeamIdentifier=")), "")
    if not re.fullmatch(r"[A-Z0-9]{10}", team):
        raise SystemExit("The signed app has no Apple Developer Team identifier.")
    # The app ticket is retained by both ZIP variants and by the app copied out of the DMG.
    with TemporaryDirectory(dir=BUILD, prefix="notary-") as temporary:
        to_submit = Path(temporary) / f"BasisCharacter-{VERSION}.zip"
        archive_bundle(APP, to_submit)
        submission_id = notarize(to_submit, APP, profile, keychain)
    # Signed archives are only moved into dist after verify_archive checks these claims.
    report.update(signature="Developer ID Application", teamIdentifier=team,
                  notarized=True, notarizationId=submission_id, stapled=True, gatekeeper="passed")
    signing_note = "应用使用 Apple Developer ID 签名，并附有 Apple 公证凭据。"
report_path = DIST / "macos-package-check.json"
report_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
readme = f"""点群与基函数 {VERSION} — Mac Apple 芯片整合版

适用：Apple 芯片 Mac，macOS 12 或更新版本。
解压后打开 BasisCharacter.app。可以将它放入“应用程序”文件夹。
无需 Python、Node、浏览器或联网。

右上角或 Mac“语言”菜单可切换简体中文、繁体中文和 English，保留输入和结果并记住选择。
“从基函数计算”：87 个已验证空间点群；s/p/五维实 d → 可约特征标 → 全体与各封闭块的不可约组成。
“手动输入特征标”：保留原程序 423 个点群和完整复不可约表示表，支持数值与复数表达式。
在基函数分解后点击“生成 SALC 系数”，即可逐个不可约表示和副本查看、复制系数。
“振动光谱（红外与拉曼）”从全部原子坐标求振动自由度、基频对称性和光谱活性。
各入口使用统一的共轭类约定，支持复制文本和 LaTeX、保存输入及导出结果。
旧版 0.1–0.3 输入仍可载入，载入后重新计算。
offline 文件夹包含可切换三语的离线 HTML。

{signing_note}
已通过源代码自动化测试、原程序数学数据交叉核验及封装资源与签名校验。
Apple JavaScriptCore 自检涵盖七个整合示例、87 个空间点群 p/d 表示、423 张约化表与三种语言。
桌面窗口、系统文件对话框的实际交互尚未由自动化视觉检查验证。
"""
def archive_app(destination, offline_pages, *, full=False):
    suffix = "" if full else "-lite"
    archive = destination / f"BasisCharacter-{VERSION}-macOS-arm64{suffix}.zip"
    archive_bundle(APP, archive)
    with zipfile.ZipFile(archive, "a", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        out.writestr("使用说明.txt", readme)
        out.writestr("README-English.txt", (ROOT/"README.en.md").read_text(encoding='utf-8'))
        out.writestr("使用說明.txt", (ROOT/"README.zh-Hant.md").read_text(encoding='utf-8'))
        out.write(ROOT / "SIGNING.md", "SIGNING.md")
        for page in offline_pages:
            out.write(page, "offline/" + page.name)
        for path in sorted((ROOT / "examples").glob("*.json")):
            out.write(path, "examples/" + path.name)
        out.writestr(report_path.name, report_json)
    verify_archive(archive, report["appExecutableSha256"], distribution=args.sign_and_notarize)
    return archive


with TemporaryDirectory(dir=DIST, prefix="macos-packages-") as temporary:
    destination = Path(temporary)
    archives = [archive_app(destination, [bundle])]
    if args.with_full:
        archives.append(archive_app(destination, language_pages(bundle.read_text(encoding="utf-8")), full=True))
    if args.with_dmg:
        image, image_report = build_disk_image(destination, report, identity, profile, keychain)
        archives.append(image)
    results = [{"archive": archive.name, "bytes": archive.stat().st_size, "sha256": sha256(archive)}
               for archive in archives]
    for archive in archives:
        archive.replace(DIST / archive.name)
if args.with_dmg:
    (DIST / "macos-dmg-check.json").write_text(json.dumps(image_report, indent=2) + "\n", encoding="utf-8")
report_path.write_text(report_json, encoding="utf-8")
checksums = [sha256(path) + "  " + str(path.relative_to(DIST))
             for path in sorted(APP.rglob("*")) if path.is_file()]
checksums.extend(f"{result['sha256']}  {result['archive']}" for result in results)
(DIST / "MACOS-SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
print(json.dumps({"app": str(APP), "packages": results, "selfCheck": "passed"}, ensure_ascii=False, indent=2))
