"""Build a standalone arm64 macOS app with system AppKit/WebKit.

No pip/npm install, network access, or dependency on Point Group Reducer.
"""
import argparse
from pathlib import Path
import datetime
import json
import os
import plistlib
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import DIST, VERSION, build_html, language_pages, sha256

BUILD = ROOT / "build" / "macos-arm64"
APP = DIST / "BasisCharacter.app"


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--with-full", action="store_true", help="Also build the ZIP with three language-specific offline pages.")
args = parser.parse_args()
if sys.platform != "darwin":
    raise SystemExit("This builder requires macOS and Apple's command line tools.")
BUILD.mkdir(parents=True, exist_ok=True)
bundle = build_html()
if APP.exists():
    info = plistlib.loads((APP / "Contents" / "Info.plist").read_bytes())
    if info.get("CFBundleIdentifier") != "org.symmetrygroup.basischaracter.prototype":
        raise SystemExit("Refusing to replace a different application.")
    shutil.rmtree(APP)
macos = APP / "Contents" / "MacOS"
resources = APP / "Contents" / "Resources"
macos.mkdir(parents=True)
resources.mkdir()
shutil.copy2(bundle, resources / "index.html")
shutil.copy2(ROOT / "packaging" / "self-check.js", resources)
for language, display in {"zh-Hans":"点群与基函数","zh-Hant":"點群與基函數","en":"Point Groups & Basis Functions"}.items():
    folder=resources/(language+".lproj");folder.mkdir()
    (folder/"InfoPlist.strings").write_text('"CFBundleDisplayName" = '+json.dumps(display,ensure_ascii=False)+';\n',encoding='utf-8')
info = {
    "CFBundleName": "BasisCharacter", "CFBundleDisplayName": "点群与基函数",
    "CFBundleIdentifier": "org.symmetrygroup.basischaracter.prototype",
    "CFBundleExecutable": "BasisCharacter", "CFBundlePackageType": "APPL",
    "CFBundleShortVersionString": VERSION, "CFBundleVersion": "8",
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
run(["codesign", "--force", "--sign", "-", "--timestamp=none", str(APP)])
run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(APP)])
check = subprocess.check_output([str(macos / "BasisCharacter"), "--self-check"], text=True)
report = json.loads(check)
report.update({"date": datetime.date.today().isoformat(), "architecture": "arm64", "minimumMacOS": "12.0",
               "signature": "ad-hoc local signature", "notarized": False})
report_path = DIST / "macos-package-check.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
readme = f"""点群与基函数 {VERSION} — Mac Apple 芯片整合版

适用：Apple 芯片 Mac，macOS 12 或更新版本。
解压后打开 BasisCharacter.app。可以将它放入“应用程序”文件夹。
无需 Python、Node、浏览器或联网。

右上角或 Mac“语言”菜单可切换简体中文、繁体中文和 English，保留输入和结果并记住选择。
“从基函数计算”：87 个已验证空间点群；s/p/五维实 d → 可约特征标 → 全体与各封闭块的不可约组成。
“手动输入特征标”：保留原程序 423 个点群和完整复不可约表示表，支持数值与复数表达式。
两种入口使用同一共轭类约定、MathML 数学排版和结果格式；可复制文本/LaTeX、保存输入及导出完整结果。
旧版 0.1–0.3 输入仍可载入，载入后重新计算。尚未计算 SALC 系数或电子能量。
offline 文件夹包含可切换三语的离线 HTML。

此包使用本地临时签名，尚未经过 Apple 开发者签名和公证。
已通过源代码自动化测试、原程序数学数据交叉核验及封装资源与签名校验。
Apple JavaScriptCore 自检涵盖七个整合示例、87 个空间点群 p/d 表示、423 张约化表与三种语言。
桌面窗口、系统文件对话框的实际交互尚未由自动化视觉检查验证。
"""
def archive_app(offline_pages, *, full=False):
    suffix = "" if full else "-lite"
    archive = DIST / f"BasisCharacter-{VERSION}-macOS-arm64{suffix}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for path in sorted(APP.rglob("*")):
            if path.is_file():
                out.write(path, str(path.relative_to(DIST)))
        out.writestr("使用说明.txt", readme)
        out.writestr("README-English.txt", (ROOT/"README.en.md").read_text(encoding='utf-8'))
        out.writestr("使用說明.txt", (ROOT/"README.zh-Hant.md").read_text(encoding='utf-8'))
        for page in offline_pages:
            out.write(page, "offline/" + page.name)
        for path in sorted((ROOT / "examples").glob("*.json")):
            out.write(path, "examples/" + path.name)
        out.write(report_path, report_path.name)
    return archive


archives = [archive_app([bundle])]
if args.with_full:
    archives.append(archive_app(language_pages(bundle.read_text(encoding="utf-8")), full=True))
results = [{"archive": archive.name, "bytes": archive.stat().st_size, "sha256": sha256(archive)} for archive in archives]
checksums = [sha256(path) + "  " + str(path.relative_to(DIST))
             for path in sorted(APP.rglob("*")) if path.is_file()]
checksums.extend(f"{result['sha256']}  {result['archive']}" for result in results)
(DIST / "MACOS-SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
print(json.dumps({"app": str(APP), "packages": results, "selfCheck": "passed"}, ensure_ascii=False, indent=2))
