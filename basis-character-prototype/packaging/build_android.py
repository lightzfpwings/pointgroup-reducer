"""Build an aligned Android APK containing the integrated offline page."""
import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import DIST, VERSION, build_html, sha256

ANDROID = ROOT / "packaging" / "android"
PACKAGE = "io.github.lightzfpwings.basischaracter"
MIN_API = 26
TARGET_API = 35
TOOLS_VERSION = "35.0.0"


def run(cmd, **kwargs):
    return subprocess.run([str(arg) for arg in cmd], check=True, **kwargs)


def output(cmd):
    return run(cmd, capture_output=True, text=True).stdout


def version_code(version):
    major, minor, patch = (int(n) for n in version.split("."))
    if minor >= 1000 or patch >= 1000:
        raise ValueError("Minor and patch components must be below 1000.")
    return major * 1000000 + minor * 1000 + patch


def build_apk(sdk, work, manifest, sources, target, assets=None, version=VERSION):
    tools = sdk / "build-tools" / TOOLS_VERSION
    jar = sdk / "platforms" / f"android-{TARGET_API}" / "android.jar"
    aapt = tools / "aapt2"
    work.mkdir()
    classes = work / "classes"
    classes.mkdir()
    shell = work / "shell.apk"
    generated = work / "gen"
    generated.mkdir()
    link = [aapt, "link", "-o", shell, "-I", jar, "--manifest", manifest,
            "--min-sdk-version", str(MIN_API), "--target-sdk-version", str(TARGET_API),
            "--version-name", version, "--version-code", str(version_code(version))]
    if assets:
        resources = work / "resources.zip"
        run([aapt, "compile", "--dir", ANDROID / "res", "-o", resources])
        link += ["--java", generated, "-A", assets, resources]
    run(link)
    src = [*sources.glob("*.java"), *generated.rglob("*.java")]
    # javac needs the Java 8 LambdaMetafactory signatures; the Android stubs
    # intentionally omit them. D8 desugars the resulting lambda call sites.
    run(["javac", "-encoding", "UTF-8", "--release", "8", "-classpath", jar, "-d", classes, *src])
    class_jar = work / "code.jar"
    with zipfile.ZipFile(class_jar, "w") as archive:
        for path in sorted(classes.rglob("*.class")):
            archive.write(path, path.relative_to(classes).as_posix())
    dex = work / "dex"
    dex.mkdir()
    run([tools / "d8", "--release", "--min-api", str(MIN_API), "--lib", jar, "--output", dex, class_jar])
    with zipfile.ZipFile(shell, "a", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(dex.glob("*.dex")):
            archive.write(path, path.name)
    run([tools / "zipalign", "-f", "-P", "16", "4", shell, target])
    run([tools / "zipalign", "-c", "-P", "16", "4", target])


def verify_apk(sdk, apk, html):
    info = output([sdk / "build-tools" / TOOLS_VERSION / "aapt", "dump", "badging", apk])
    for entry in (f"package: name='{PACKAGE}'", f"versionCode='{version_code(VERSION)}'",
                  f"versionName='{VERSION}'", f"sdkVersion:'{MIN_API}'", f"targetSdkVersion:'{TARGET_API}'",
                  f"launchable-activity: name='{PACKAGE}.MainActivity'"):
        if entry not in info:
            raise ValueError(f"APK missing expected metadata: {entry}")
    permissions = set(re.findall(r"^uses-permission: name='([^']+)'", info, re.MULTILINE))
    if permissions != {"android.permission.INTERNET", "android.permission.REQUEST_INSTALL_PACKAGES"}:
        raise ValueError(f"Unexpected Android update permissions: {permissions}")
    with zipfile.ZipFile(apk) as z:
        if z.testzip() or not z.read("classes.dex").startswith(b"dex\n"):
            raise ValueError("Invalid APK or missing DEX")
        if any(name.startswith("lib/") for name in z.namelist()):
            raise ValueError("This universal Java APK should have no ABI-specific libraries.")
        if z.read("assets/index.html") != html.read_bytes() or z.read("assets/bridge.js") != (ANDROID / "bridge.js").read_bytes():
            raise ValueError("Packaged app resources differ from the offline build.")
    return {"version": VERSION, "versionCode": version_code(VERSION), "package": PACKAGE,
            "minimumAPI": MIN_API, "targetAPI": TARGET_API, "architecture": "universal",
            "offlinePageSha256": sha256(html), "unsignedApkSha256": sha256(apk)}


def emulator_test(sdk, work, avd, unsigned):
    tools = sdk / "build-tools" / TOOLS_VERSION
    adb = sdk / "platform-tools" / "adb"
    emulator = sdk / "emulator" / "emulator"
    port = 5586
    serial = f"emulator-{port}"
    if serial in output([adb, "devices"]):
        raise RuntimeError(f"Emulator port {port} already in use.")
    # Both versions and the instrumentation use an ephemeral key. Only the
    # original production APK is exported to dist.
    key = work / "instrumentation-only.p12"
    run(["keytool", "-genkeypair", "-keystore", key, "-storepass", "ci-test-only",
         "-keypass", "ci-test-only", "-storetype", "PKCS12", "-alias", "smoke",
         "-keyalg", "RSA", "-keysize", "2048", "-validity", "3", "-dname", "CN=Instrumentation test only"])
    def signed(src, dest):
        run([tools / "apksigner", "sign", "--ks", key, "--ks-pass", "pass:ci-test-only",
             "--v4-signing-enabled", "false", "--out", dest, src])
        run([tools / "apksigner", "verify", dest])
        return dest
    next_code = version_code(VERSION)+1
    next_version = f"{next_code//1000000}.{next_code//1000%1000}.{next_code%1000}"
    fixture = work / "fixture-unsigned.apk"
    build_apk(sdk, work/"fixture", ANDROID/"AndroidManifest.xml", ANDROID/"src", fixture, work/"assets", next_version)
    test_assets = work/"instrumentation-assets"
    test_assets.mkdir()
    signed(fixture, test_assets/"fixture.apk")
    test_unsigned = work / "instrumentation-unsigned.apk"
    build_apk(sdk, work / "instrumentation", ANDROID / "test" / "AndroidManifest.xml", ANDROID / "test", test_unsigned, test_assets)
    test_packages = [signed(src, work/("smoke-"+src.name)) for src in (unsigned, test_unsigned)]
    log = DIST / "android-emulator.log"
    with log.open("w") as stream:
        process = subprocess.Popen([str(emulator), "-avd", avd, "-port", str(port),
                                    "-no-window", "-no-audio", "-no-boot-anim", "-no-snapshot",
                                    "-gpu", "swiftshader_indirect"], stdout=stream, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline and process.poll() is None:
                boot = subprocess.run([adb, "-s", serial, "shell", "getprop", "sys.boot_completed"],
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                if boot.stdout.strip() == "1":
                    break
                time.sleep(2)
            else:
                raise RuntimeError("Android emulator failed to boot: " + log.read_text(errors="replace")[-2500:])
            device = [adb, "-s", serial]
            run([*device, "shell", "input", "keyevent", "82"])
            for apk in test_packages:
                run([*device, "install", "-r", apk])
            run_result = run([*device, "shell", "am", "instrument", "-w", "-r", PACKAGE + ".test/.SmokeTest"],
                             timeout=150, capture_output=True, text=True).stdout
            print(run_result)
            if "BASIS_SMOKE_OK" not in run_result or "INSTRUMENTATION_CODE: -1" not in run_result:
                print(output([*device, "logcat", "-d", "-t", "250", "-s", "AndroidRuntime:E", "chromium:E", "ActivityTaskManager:E"]))
                raise RuntimeError("Android runtime smoke failed.")
            run([*device,"shell","appops","set",PACKAGE,"REQUEST_INSTALL_PACKAGES","allow"])
            runner = PACKAGE+".test/.UpgradeTest"
            with (work/"upgrade-run.log").open("w") as capture:
                upgrading = subprocess.Popen([str(x) for x in [*device,"shell","am","instrument","-w","-r","-e","version",next_version,runner]], stdout=capture, stderr=capture)
                try:
                    deadline = time.monotonic()+85
                    while time.monotonic()<deadline:
                        info = output([*device,"shell","dumpsys","package",PACKAGE])
                        if f"versionCode={next_code} " in info:
                            break
                        if upgrading.poll() is not None:
                            raise RuntimeError("Upgrade instrumentation exited: "+(work/"upgrade-run.log").read_text()[-2500:])
                        # Accept only the system package installer's explicit Install button.
                        subprocess.run([*device,"shell","uiautomator","dump","/sdcard/basis-update-ui.xml"],capture_output=True,timeout=15)
                        tree = subprocess.run([*device,"shell","cat","/sdcard/basis-update-ui.xml"],capture_output=True,text=True).stdout
                        if tree.startswith("<?xml"):
                            for node in ET.fromstring(tree).iter("node"):
                                if (node.get("package","").endswith("packageinstaller") and node.get("text","").lower()=="install"
                                        and node.get("enabled")=="true"):
                                    x1,y1,x2,y2=map(int,re.findall(r"\d+",node.get("bounds","")))
                                    run([*device,"shell","input","tap",str((x1+x2)//2),str((y1+y2)//2)])
                                    break
                        time.sleep(1)
                    else:
                        raise RuntimeError("System APK upgrade timed out: "+(work/"upgrade-run.log").read_text()[-2000:])
                finally:
                    if upgrading.poll() is None:
                        upgrading.terminate()
                    upgrading.wait(timeout=10)
            verify = output([*device,"shell","am","instrument","-w","-r","-e","phase","verify",runner])
            if "BASIS_UPGRADE_PRESERVED" not in verify or "INSTRUMENTATION_CODE: -1" not in verify:
                raise RuntimeError("Application data verification failed: "+verify)
            return {"passed": True, "deviceAPI": output([*device, "shell", "getprop", "ro.build.version.sdk"]).strip(),
                    "checks": ["launcher", "water-SALCs", "clipboard", "open-project-picker", "save-project-picker",
                               "formula-selection", "structure-review", "IR-Raman-activity", "XYZ-file-picker", "mobile-layout",
                               "update-digest-rejection", "system-upgrade", "update-preserves-data"]}
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT"))
    parser.add_argument("--smoke", action="store_true", help="Run an instrumented Android emulator test with an ephemeral test-only key.")
    parser.add_argument("--avd", default="basis-smoke")
    args = parser.parse_args()
    if args.sdk is None:
        parser.error("Set ANDROID_HOME or pass --sdk with Android platform 35 and build-tools 35.0.0.")
    sdk = args.sdk.resolve()
    html = build_html()
    DIST.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="basis-android-") as temporary:
        work = Path(temporary)
        assets = work / "assets"
        assets.mkdir()
        shutil.copyfile(html, assets / "index.html")
        shutil.copyfile(ANDROID / "bridge.js", assets / "bridge.js")
        unsigned = work / f"BasisCharacter-{VERSION}-Android-unsigned.apk"
        build_apk(sdk, work / "app", ANDROID / "AndroidManifest.xml", ANDROID / "src", unsigned, assets)
        report = verify_apk(sdk, unsigned, html)
        if args.smoke:
            report["runtimeTest"] = emulator_test(sdk, work, args.avd, unsigned)
        shutil.copyfile(unsigned, DIST / unsigned.name)
        (DIST / "android-package-check.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
