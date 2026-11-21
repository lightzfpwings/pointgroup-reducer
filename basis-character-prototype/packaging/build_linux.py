"""Build the installable Debian/Ubuntu desktop launcher and offline application."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import DIST, VERSION, build_html

PACKAGE = "basis-character"
LINUX = ROOT / "packaging" / "linux"


def build():
    page = build_html()
    destination = DIST / f"BasisCharacter-{VERSION}-Linux-all.deb"
    with TemporaryDirectory(dir=DIST) as temporary:
        work = Path(temporary)
        stage = work / PACKAGE
        payload = {
            "usr/lib/basis-character/update.py": (LINUX / "update.py", 0o755),
            "usr/share/applications/basis-character-update.desktop": (LINUX / "basis-character-update.desktop", 0o644),
            "usr/bin/basis-character": (LINUX / "basis-character.sh", 0o755),
            "usr/share/applications/basis-character.desktop": (LINUX / "basis-character.desktop", 0o644),
            "usr/share/icons/hicolor/512x512/apps/basis-character.png": (ROOT / "packaging/icons/basis-character-512.png", 0o644),
            "usr/share/basis-character/index.html": (page, 0o644),
        }
        installed_size = 0
        for name, (source, mode) in payload.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(mode)
            installed_size += (target.stat().st_size + 1023) // 1024
        metadata = stage / "DEBIAN"
        metadata.mkdir()
        # dpkg-deb requires control-directory permissions even under a strict umask.
        for directory in [stage, *[path for path in stage.rglob("*") if path.is_dir()]]:
            directory.chmod(0o755)
        control = metadata / "control"
        control.write_text(
            f"Package: {PACKAGE}\n"
            f"Version: {VERSION}\n"
            "Section: science\n"
            "Priority: optional\n"
            "Architecture: all\n"
            "Maintainer: lightzfpwings <209329913+lightzfpwings@users.noreply.github.com>\n"
            f"Installed-Size: {installed_size}\n"
            "Depends: xdg-utils, desktop-file-utils, python3 (>= 3.9), ca-certificates, pkexec | policykit-1, zenity\n"
            "Recommends: firefox-esr | firefox | chromium | chromium-browser | google-chrome-stable\n"
            "Homepage: https://github.com/lightzfpwings/pointgroup-reducer\n"
            "Description: Offline point group characters, SALCs and vibrational symmetry\n"
            " Calculate characters, SALC coefficients and IR/Raman selection rules\n"
            " in English, Simplified Chinese or Traditional Chinese. The desktop menu\n"
            " opens the included offline application in a modern graphical web browser.\n",
            encoding="utf-8",
        )
        control.chmod(0o644)
        built = work / destination.name
        subprocess.run(["dpkg-deb", "--root-owner-group", "-Zxz", "--build", stage, built], check=True)
        for field, expected in [("Package", PACKAGE), ("Version", VERSION), ("Architecture", "all")]:
            value = subprocess.check_output(["dpkg-deb", "-f", built, field], text=True).strip()
            if value != expected:
                raise ValueError(f"Unexpected {field}: {value}")
        os.replace(built, destination)
    print(destination)
    return destination


if __name__ == "__main__":
    build()
