"""Publish the verified integrated desktop, offline, and source distributions."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from publish_release import api, upload_asset

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "basis-character-prototype"
ASSETS = ROOT / "release-assets"
LANGUAGES = ("zh-Hans", "zh-Hant", "en")
INSTALLER = "BasisCharacter/MicrosoftEdgeWebView2RuntimeInstallerX64.exe"


def digest(source):
    result = hashlib.sha256()
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
        result.update(chunk)
    return result.hexdigest()


def file_digest(path):
    with path.open("rb") as source:
        return digest(source)


def checked_assets(version):
    checks = {}
    offline_name = f"BasisCharacterPrototype-{version}"
    for platform, checksum_file in (("Windows-x64", "WINDOWS"), ("macOS-arm64", "MACOS")):
        sums = {name: value for value, name in
                (line.split("  ", 1) for line in (ASSETS / f"{checksum_file}-SHA256SUMS.txt").read_text().splitlines())}
        windows = platform == "Windows-x64"
        executable = "BasisCharacter/BasisCharacter.exe" if windows else "BasisCharacter.app/Contents/MacOS/BasisCharacter"
        prefix = "BasisCharacter/" if windows else ""
        binaries = []
        for suffix in ("", "-lite"):
            path = ASSETS / f"BasisCharacter-{version}-{platform}{suffix}.zip"
            checks[path] = file_digest(path)
            assert checks[path] == sums[path.name], path.name
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None, path.name
                report = json.loads(archive.read(prefix + ("windows" if windows else "macos") + "-package-check.json"))
                assert report["status"] == "passed" and report["version"] == report["reductionVersion"] == version, path.name
                assert report["supportedPointGroups"] == 87 and len(report["reductionTables"]) == 423, path.name
                assert len(report["languages"]) == 3, path.name
                actual_pages = {name for name in archive.namelist() if name.startswith(prefix + "offline/")}
                pages = [offline_name] if suffix else [f"{offline_name}-{language}" for language in LANGUAGES]
                assert actual_pages == {f"{prefix}offline/{page}.html" for page in pages}, path.name
                with archive.open(executable) as source:
                    binaries.append(digest(source))
                if windows and not suffix:
                    runtime = report["webview2OfflineInstaller"]
                    assert runtime["status"] == "passed" and runtime["signature"] == "Valid", path.name
                    with archive.open(INSTALLER) as source:
                        assert digest(source) == runtime["sha256"], path.name
                else:
                    assert INSTALLER not in archive.namelist(), path.name
        assert binaries[0] == binaries[1], platform

    manifest = json.loads((ASSETS / "manifest.json").read_text())
    assert manifest["version"] == version
    files = {item["name"]: item for item in manifest["files"]}
    for name in [f"{offline_name}-{language}.html" for language in LANGUAGES] + [f"{offline_name}-source.zip"]:
        path = ASSETS / name
        checks[path] = file_digest(path)
        assert path.stat().st_size == files[name]["bytes"] and checks[path] == files[name]["sha256"], name
    checksums = ASSETS / "SHA256SUMS.txt"
    checksums.write_text("".join(f"{value}  {path.name}\n" for path, value in checks.items()), encoding="utf-8")
    checks[checksums] = file_digest(checksums)
    return checks


def change_release(endpoint, method, payload):
    return json.loads(subprocess.check_output(
        ["gh", "api", "--method", method, endpoint, "--input", "-"],
        input=json.dumps(payload), text=True, encoding="utf-8",
    ))


def verify_upload(asset, path, digest_value):
    assert asset["name"] == path.name
    assert asset["state"] == "uploaded" and asset["size"] == path.stat().st_size, path.name
    assert asset["digest"] == "sha256:" + digest_value, path.name


def main():
    version = json.loads((APP / "package.json").read_text())["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version
    tag = "basis-v" + version
    sha = os.environ["GITHUB_SHA"]
    repo = os.environ["GH_REPO"]
    base = f"repos/{repo}/releases"
    refs = api(f"repos/{repo}/git/matching-refs/tags/{tag}")
    for ref in refs:
        if ref["ref"] == "refs/tags/" + tag:
            target = ref["object"]
            if target["type"] == "tag":
                target = api(f"repos/{repo}/git/tags/{target['sha']}")["object"]
            assert target["type"] == "commit" and target["sha"] == sha, "Existing tag points to another commit"

    checks = checked_assets(version)
    releases = [release for release in api(base + "?per_page=100") if release["tag_name"] == tag]
    assert len(releases) <= 1, "More than one release uses the version tag"
    if releases:
        release = releases[0]
        assert release["target_commitish"] == sha, "Existing release targets another commit"
        if not release["draft"]:
            assert {entry["name"] for entry in release["assets"]} == {path.name for path in checks}
            print(release["html_url"])
            return
    else:
        release = change_release(base, "POST", {
            "tag_name": tag, "target_commitish": sha, "name": f"Point Groups & Basis Functions {version}",
            "body": (APP / "RELEASE_NOTES.md").read_text(encoding="utf-8"), "draft": True,
        })

    endpoint = f"{base}/{release['id']}"
    existing = {asset["name"]: asset for asset in api(endpoint)["assets"]}
    for path, digest_value in checks.items():
        if path.name in existing:
            verify_upload(existing[path.name], path, digest_value)
        else:
            verify_upload(upload_asset(release, path), path, digest_value)
    confirmed = {asset["name"]: asset for asset in api(endpoint)["assets"]}
    assert confirmed.keys() == {path.name for path in checks}, "Unexpected draft assets"
    for path, digest_value in checks.items():
        verify_upload(confirmed[path.name], path, digest_value)
    published = change_release(endpoint, "PATCH", {"draft": False, "prerelease": False, "make_latest": "true"})
    assert not published["draft"] and published["tag_name"] == tag
    print(published["html_url"])


if __name__ == "__main__":
    main()
