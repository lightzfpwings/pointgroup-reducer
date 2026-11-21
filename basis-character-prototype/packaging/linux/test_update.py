import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("basis_linux_update", Path(__file__).with_name("update.py"))
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

class UpdateTest(unittest.TestCase):
    def test_handler(self):
        self.assertEqual(updater.parse_link("basis-character-update://install/0.10.0?lang=zh-Hant"),("0.10.0",1))
        for link in ["basis-character-update://foreign/0.7.1","basis-character-update://install/../file","basis-character-update://install/0.7.1-rc"]:
            with self.assertRaises(ValueError): updater.parse_link(link)
        self.assertGreater(updater.parts("0.10.0"),updater.parts("0.9.9"))

    def test_package_integrity(self):
        data = b"test package"
        tag = "basis-v0.8.0"
        name = "BasisCharacter-0.8.0-Linux-all.deb"
        asset = dict(name=name, state="uploaded", size=len(data), digest="sha256:"+hashlib.sha256(data).hexdigest(),
                     browser_download_url=f"https://github.com/{updater.REPO}/releases/download/{tag}/{name}")
        def fetch(url):
            if url.endswith("/tags/"+tag):
                return io.BytesIO(json.dumps(dict(tag_name=tag,draft=False,prerelease=False,assets=[asset])).encode())
            self.assertEqual(url,asset["browser_download_url"])
            return io.BytesIO(data)
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t)/"release.deb"
            updater.download("0.8.0",dest,fetch)
            self.assertEqual(dest.read_bytes(),data)
            asset["digest"]="sha256:"+"0"*64
            with self.assertRaises(ValueError): updater.download("0.8.0",Path(t)/"bad.deb",fetch)

    @unittest.skipUnless(shutil.which("dpkg-deb") and os.geteuid()==0, "requires an isolated Debian package database")
    def test_real_dpkg_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"root"
            (root/"var/lib/dpkg/updates").mkdir(parents=True)
            (root/"var/lib/dpkg/status").touch()
            stage = Path(tmp)/"package"
            (stage/"DEBIAN").mkdir(parents=True)
            program = stage/"usr/share/basis-character/app-version"
            program.parent.mkdir(parents=True)
            def package(version):
                program.write_text(version)
                (stage/"DEBIAN/control").write_text(f"Package: basis-character\nVersion: {version}\nArchitecture: all\nMaintainer: Test <test@example.org>\nDescription: Isolated update fixture\n")
                deb = Path(tmp)/(version+".deb")
                subprocess.run(["dpkg-deb","--build",stage,deb],check=True,capture_output=True)
                return deb
            with patch.dict(os.environ,{"DPKG_ROOT":str(root)}):
                subprocess.run(["dpkg","--install",package("0.7.0")],check=True,capture_output=True)
                project = root/"user-project.json";project.write_text("project")
                newer = package("0.7.1").read_bytes()
                tag,name = "basis-v0.7.1","BasisCharacter-0.7.1-Linux-all.deb"
                direct = f"https://github.com/{updater.REPO}/releases/download/{tag}/{name}"
                a = dict(name=name,browser_download_url=direct,size=len(newer),state="uploaded",digest="sha256:"+hashlib.sha256(newer).hexdigest())
                metadata = json.dumps(dict(tag_name=tag,draft=False,prerelease=False,assets=[a])).encode()
                def fetch(url): return io.BytesIO(newer if url==direct else metadata)
                updater.install("0.7.1",fetch)
                self.assertEqual((root/"usr/share/basis-character/app-version").read_text(),"0.7.1")
                self.assertEqual(project.read_text(),"project")
                with self.assertRaises(ValueError): updater.install("0.7.1",fetch)
