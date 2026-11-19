"""Portable packaging safety checks; real trust verification requires Windows."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PACKAGING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGING))

spec = importlib.util.spec_from_file_location("build_windows", PACKAGING / "build_windows.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackagingContractTests(unittest.TestCase):
    def test_development_mode_has_no_signing_dependency(self):
        args = builder.parse_args([])
        with patch.object(builder, "powershell", side_effect=AssertionError("Must not request signing")):
            report = builder.authenticate_application(Path("unused"), args)
        self.assertEqual(report, {"status": "not-requested", "mode": "development", "files": []})

    def test_signed_release_needs_explicit_publisher(self):
        for arguments in (["--require-signature"], ["--sign-machine-store"], ["--sign-thumbprint", "no"]):
            with self.subTest(arguments=arguments), patch("sys.stderr"), self.assertRaises(SystemExit):
                builder.parse_args(arguments)

    def test_store_and_external_signing_arguments(self):
        self.assertTrue(builder.parse_args(["--build-only"]).build_only)
        self.assertTrue(builder.parse_args(["--package-only", "--require-signature", "--expected-signer-subject", "CN=Publisher"]).package_only)
        self.assertEqual(builder.parse_args(["--sign-thumbprint", "a" * 40]).sign_thumbprint, "a" * 40)
        with patch("sys.stderr"), self.assertRaises(SystemExit):
            builder.parse_args(["--build-only", "--package-only"])

    def test_signature_report_binds_publisher_timestamp_and_final_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            build = Path(directory)
            package = build / "BasisCharacter"
            package.mkdir()
            entries = []
            for name in builder.APPLICATION_BINARIES:
                binary = package / name
                binary.write_bytes(b"test binary")
                entries.append({"path": name, "sha256": builder.sha256(binary), "subject": "CN=Publisher",
                                "thumbprint": "A" * 40, "timestampSubject": "CN=Timestamp", "timestampThumbprint": "B" * 40})
            report = {"status": "passed", "mode": "external", "files": entries}

            def write_report(*args, **kwargs):
                (build / "authenticode-check.json").write_text(json.dumps(report))

            args = builder.parse_args(["--package-only", "--require-signature", "--expected-signer-subject", "CN=Publisher"])
            with patch.object(builder, "BUILD", build), patch.object(builder, "powershell", return_value=("pwsh", {})), \
                 patch.object(builder, "find_signtool", return_value="signtool.exe"), \
                 patch.object(builder.subprocess, "run", side_effect=write_report):
                self.assertEqual(builder.authenticate_application(package, args), report)
                (package / builder.APPLICATION_BINARIES[0]).write_bytes(b"changed after verification")
                with self.assertRaisesRegex(SystemExit, "changed"):
                    builder.authenticate_application(package, args)
                (package / builder.APPLICATION_BINARIES[0]).write_bytes(b"test binary")
                del entries[0]["timestampSubject"]
                with self.assertRaisesRegex(SystemExit, "timestamp"):
                    builder.authenticate_application(package, args)

    def test_failed_external_verification_cannot_produce_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build, dist = root / "build", root / "dist"
            package = build / "BasisCharacter"
            package.mkdir(parents=True)
            dist.mkdir()
            for name in builder.APPLICATION_BINARIES:
                (package / name).write_bytes(b"not signed")
            (dist / f"BasisCharacterPrototype-{builder.VERSION}.html").write_text("test")
            stale = dist / f"BasisCharacter-{builder.VERSION}-Windows-x64-lite.zip"
            stale.write_bytes(b"old archive")
            args = builder.parse_args(["--package-only", "--require-signature", "--expected-signer-subject", "CN=Publisher"])
            with patch.object(builder, "BUILD", build), patch.object(builder, "DIST", dist), \
                 patch.object(builder.sys, "platform", "win32"), patch.dict(builder.os.environ, {"PROCESSOR_ARCHITECTURE": "AMD64"}), \
                 patch.object(builder, "parse_args", return_value=args), \
                 patch.object(builder, "authenticate_application", side_effect=RuntimeError("Untrusted signature")), \
                 patch.object(builder, "archive_distribution") as archive, patch.object(builder.subprocess, "run") as run:
                with self.assertRaisesRegex(RuntimeError, "Untrusted"):
                    builder.main()
                archive.assert_not_called()
                run.assert_not_called()
                self.assertFalse(stale.exists())

    def test_repackaging_full_build_keeps_signed_binaries_and_lite_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "BasisCharacter"
            offline = package / "offline"
            offline.mkdir(parents=True)
            bundle = root / "BasisCharacterPrototype-test.html"
            bundle.write_text("all three languages")
            for name in builder.APPLICATION_BINARIES:
                (package / name).write_bytes(b"signed binary stays unchanged")
            for language in ("zh-Hans", "zh-Hant", "en"):
                (offline / f"{bundle.stem}-{language}.html").write_text("full package")
            (package / builder.WEBVIEW2_INSTALLER).write_bytes(b"Microsoft installer")
            builder.prepare_lite_resources(package, bundle)
            self.assertEqual([path.name for path in offline.iterdir()], [bundle.name])
            self.assertFalse((package / builder.WEBVIEW2_INSTALLER).exists())
            for name in builder.APPLICATION_BINARIES:
                self.assertEqual((package / name).read_bytes(), b"signed binary stays unchanged")


if __name__ == "__main__":
    unittest.main()
