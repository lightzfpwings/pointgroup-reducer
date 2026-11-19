"""Build an aligned universal Android APK with the release's offline SALC page."""
import argparse
import json
import os
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


def build_apk(sdk, work, manifest, sources, target, assets=None):
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
            "--version-name", VERSION, "--version-code", str(version_code(VERSION))]
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
    if any(line.startswith("uses-permission:") for line in info.splitlines()):
        raise ValueError("The offline app unexpectedly requests an Android permission.")
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
    test_unsigned = work / "instrumentation-unsigned.apk"
    build_apk(sdk, work / "instrumentation", ANDROID / "test" / "AndroidManifest.xml",
              ANDROID / "test", test_unsigned)
    # Temporary private key and test APKs exist only inside the temporary build directory.
    key = work / "instrumentation-only.p12"
    run(["keytool", "-genkeypair", "-keystore", key, "-storepass", "ci-test-only",
         "-keypass", "ci-test-only", "-storetype", "PKCS12", "-alias", "smoke",
         "-keyalg", "RSA", "-keysize", "2048", "-validity", "3", "-dname", "CN=Instrumentation test only"])
    test_packages = []
    for src in (unsigned, test_unsigned):
        path = work / ("smoke-" + src.name)
        run([tools / "apksigner", "sign", "--ks", key, "--ks-pass", "pass:ci-test-only",
             "--v4-signing-enabled", "false", "--out", path, src])
        run([tools / "apksigner", "verify", path])
        test_packages.append(path)
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
            return {"passed": True, "deviceAPI": output([*device, "shell", "getprop", "ro.build.version.sdk"]).strip(),
                    "checks": ["launcher", "water-SALCs", "clipboard", "open-project-picker", "save-project-picker"]}
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
