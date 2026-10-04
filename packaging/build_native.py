"""Build standalone GUI and CLI on their target operating system."""
from pathlib import Path
import os
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    try:
        return subprocess.run(args, check=True, cwd=ROOT, **kwargs)
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout)
        if error.stderr:
            print(error.stderr, file=sys.stderr)
        raise


def main():
    if sys.platform not in ('win32', 'darwin'):
        raise SystemExit('Run this builder on Windows or macOS.')
    version = (ROOT / 'VERSION').read_text().strip()
    arch = platform.machine().lower()
    if arch in ('amd64', 'x86_64'):
        arch = 'x64'
    target = 'Windows' if sys.platform == 'win32' else 'macOS'
    if target == 'macOS' and arch != 'arm64':
        raise SystemExit('macOS packages support Apple Silicon (arm64) only.')
    name = f'PointGroupReducer-{version}-{target}-{arch}'
    output = ROOT / 'release' / name
    if output.exists():
        raise SystemExit(f'Output already exists; move it aside before rebuilding: {output}')
    run(sys.executable, '-m', 'unittest', '-v')
    qa_env = dict(os.environ, POINTGROUP_QA_DIR=str(ROOT / 'release' / 'gui-qa'))
    run(sys.executable, 'gui_smoke.py', env=qa_env)
    with tempfile.TemporaryDirectory(prefix='pointgroup-build-') as scratch:
        tmp = Path(scratch)
        for entry, appname, mode in [('desktop.py', 'PointGroupReducer', '--windowed'),
                                     ('pointgroup.py', 'PointGroupReducer-CLI', '--console')]:
            command = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', '--onedir',
                       mode, '--hidden-import', 'matplotlib.backends.backend_agg', '--collect-data', 'matplotlib', '--name', appname, '--distpath', str(tmp / 'dist'),
                       '--workpath', str(tmp / appname), '--specpath', str(tmp / 'spec')]
            if sys.platform == 'darwin' and mode == '--windowed':
                command.extend(['--osx-bundle-identifier', 'org.symmetrygroup.pointgroupreducer'])
            run(*command, entry)
        output.mkdir(parents=True)
        if sys.platform == 'win32':
            for appname in ('PointGroupReducer', 'PointGroupReducer-CLI'):
                shutil.copytree(tmp / 'dist' / appname, output / appname)
            gui = output / 'PointGroupReducer' / 'PointGroupReducer.exe'
            cli = output / 'PointGroupReducer-CLI' / 'PointGroupReducer-CLI.exe'
        else:
            # ditto preserves bundle symlinks and metadata on macOS.
            run('/usr/bin/ditto', str(tmp / 'dist' / 'PointGroupReducer.app'), str(output / 'PointGroupReducer.app'))
            shutil.copytree(tmp / 'dist' / 'PointGroupReducer-CLI', output / 'CLI', symlinks=True)
            shutil.copy2(ROOT / 'packaging/macos/Start-CLI.command', output / 'Start-CLI.command')
            (output / 'Start-CLI.command').chmod(0o755)
            gui = output / 'PointGroupReducer.app/Contents/MacOS/PointGroupReducer'
            cli = output / 'CLI/PointGroupReducer-CLI'
            run('/usr/bin/codesign', '--verify', '--deep', '--strict', str(output / 'PointGroupReducer.app'))
        run(str(gui), '--smoke-test', timeout=60)
        smoke = []
        for language in ('en','zh-Hans','zh-Hant'):
            for group, characters, expected in [('C2v', '5,1,1,1', '2A1 + A2 + B1 + B2')]:
                check = run(str(cli), group, '--c', characters, '--lang', language, capture_output=True, text=True, encoding='utf-8')
                assert expected in check.stdout
                smoke.append(check.stdout)
        for group, expected in [('D4h', 'A1g + B1g + B2g + Eg'), ('Ih', 'Hg')]:
            check = run(str(cli), group, '--shell', '2', capture_output=True, text=True, encoding='utf-8')
            assert expected in check.stdout
            smoke.append(check.stdout)
        conflict = subprocess.run([str(cli), 'C2v', '--c', '5,1,1,1', '--shell', '2', '--lang', 'en'],
                                  cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
        assert conflict.returncode == 1 and 'Choose only one' in conflict.stderr and 'Traceback' not in conflict.stderr
        (output / 'SMOKE-TEST.txt').write_text('\n'.join(smoke), encoding='utf-8')
        for document in ('README.md', 'README.en.md', 'README.zh-Hant.md'):
            shutil.copy2(ROOT / document, output / document)
        shutil.copy2(ROOT / 'CHANGELOG.md', output / 'CHANGELOG.md')
        meta = {'version': version, 'platform': platform.platform(), 'architecture': arch,
                'python': platform.python_version(), 'source_tests': 'passed',
                'native_gui_smoke': 'passed', 'native_cli_smoke': 'passed', 'mathtext_and_three_language_smoke': 'passed',
                'based_on_user_verified_version': '2.4.2',
                'manual_click_acceptance': False}
        (output / 'BUILD-INFO.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        dependencies = run(sys.executable, '-m', 'pip', 'freeze', capture_output=True, text=True)
        (output / 'BUILD-DEPENDENCIES.txt').write_text(dependencies.stdout, encoding='utf-8')
    if sys.platform == 'darwin':
        archive = str(output) + '.zip'
        run('/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(output), archive)
    else:
        archive = shutil.make_archive(str(output), 'zip', root_dir=output.parent, base_dir=output.name)
    path = Path(archive)
    path.with_suffix('.zip.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n')
    print(archive)


if __name__ == '__main__':
    main()
