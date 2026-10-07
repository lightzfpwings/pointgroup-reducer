"""Build a standalone arm64 macOS app with system AppKit/WebKit.

No pip/npm install, network access, or dependency on Point Group Reducer.
"""
from pathlib import Path
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build" / "macos-arm64"
VERSION = json.loads((ROOT / "package.json").read_text())["version"]
APP = DIST / "BasisCharacter.app"


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


if sys.platform != "darwin":
    raise SystemExit("This builder requires macOS and Apple's command line tools.")
DIST.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)
run([sys.executable, str(ROOT / "build.py")])
if APP.exists():
    info = plistlib.loads((APP / "Contents" / "Info.plist").read_bytes())
    if info.get("CFBundleIdentifier") != "org.symmetrygroup.basischaracter.prototype":
        raise SystemExit("Refusing to replace a different application.")
    shutil.rmtree(APP)
macos = APP / "Contents" / "MacOS"
resources = APP / "Contents" / "Resources"
macos.mkdir(parents=True)
resources.mkdir()
shutil.copy2(DIST / f"BasisCharacterPrototype-{VERSION}.html", resources / "index.html")
shutil.copy2(ROOT / "engine.js", resources / "engine.js")
shutil.copy2(ROOT / "reducer-catalog.js", resources / "reducer-catalog.js")
shutil.copy2(ROOT / "reducer-adapter.js", resources / "reducer-adapter.js")
for name in ["reduction-catalog.js", "reduction-engine.js", "messages-data.js", "i18n.js", "math-format.js"]:
    shutil.copy2(ROOT / name, resources / name)
for language, display in {"zh-Hans":"点群与基函数","zh-Hant":"點群與基函數","en":"Point Groups & Basis Functions"}.items():
    folder=resources/(language+".lproj");folder.mkdir()
    (folder/"InfoPlist.strings").write_text('"CFBundleDisplayName" = '+json.dumps(display,ensure_ascii=False)+';\n',encoding='utf-8')
info = {
    "CFBundleName": "BasisCharacter", "CFBundleDisplayName": "点群与基函数",
    "CFBundleIdentifier": "org.symmetrygroup.basischaracter.prototype",
    "CFBundleExecutable": "BasisCharacter", "CFBundlePackageType": "APPL",
    "CFBundleShortVersionString": VERSION, "CFBundleVersion": "6",
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
report.update({"date": "2026-10-07", "architecture": "arm64", "minimumMacOS": "12.0",
               "signature": "ad-hoc local signature", "notarized": False})
(ROOT / "validation" / "macos-package-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
readme = f"""点群与基函数 {VERSION} — Mac Apple 芯片整合版

适用：Apple 芯片 Mac，macOS 12 或更新版本。
解压后打开 BasisCharacter.app。可以将它放入“应用程序”文件夹。
无需 Python、Node、浏览器或联网。

右上角或 Mac“语言”菜单可切换简体中文、繁体中文和 English，保留输入和结果并记住选择。
“从基函数计算”：87 个已验证空间点群；s/p/五维实 d → 可约特征标 → 全体与各封闭块的不可约组成。
“手动输入特征标”：保留原程序 423 个点群和完整复不可约表示表，支持数值与复数表达式。
两种入口使用同一共轭类约定、MathML 数学排版和结果格式；可复制文本/LaTeX、保存输入及导出完整结果。
旧版 0.1–0.3 输入仍可载入，载入后重新计算。尚未计算 SALC 系数或电子能量。
offline 文件夹还包含三种默认语言的离线 HTML 版本。

此包使用本地临时签名，尚未经过 Apple 开发者签名和公证。
已通过源代码自动化测试、原程序数学数据交叉核验及封装资源与签名校验。
Apple JavaScriptCore 自检涵盖七个整合示例、87 个空间点群 p/d 表示、423 张约化表与三种语言。
桌面窗口、系统文件对话框的实际交互尚未由自动化视觉检查验证。
"""
archive = DIST / f"BasisCharacter-{VERSION}-macOS-arm64.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as out:
    for path in sorted(APP.rglob("*")):
        if path.is_file():
            out.write(path, str(path.relative_to(DIST)))
    out.writestr("使用说明.txt", readme)
    out.writestr("README-English.txt", (ROOT/"README.en.md").read_text(encoding='utf-8'))
    out.writestr("使用說明.txt", (ROOT/"README.zh-Hant.md").read_text(encoding='utf-8'))
    for language in ["zh-Hans","zh-Hant","en"]:
        path=DIST/f"BasisCharacterPrototype-{VERSION}-{language}.html"
        out.write(path,"offline/"+path.name)
    for path in sorted((ROOT / "examples").glob("*.json")):
        out.write(path, "examples/" + path.name)
    out.writestr("macos-package-check.json", json.dumps(report, ensure_ascii=False, indent=2))
checksums = []
for path in sorted(APP.rglob("*")):
    if path.is_file():
        checksums.append(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + str(path.relative_to(DIST)))
checksums.append(hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name)
(DIST / "MACOS-SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
print(json.dumps({"app": str(APP), "archive": str(archive), "bytes": archive.stat().st_size,
                  "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "selfCheck": "passed"}, ensure_ascii=False, indent=2))
