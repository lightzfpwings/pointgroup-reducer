"""Verify native packages, publish them, then remove obsolete release assets."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True, encoding='utf-8').strip()


def api(path):
    return json.loads(gh('api', path))


def package_checks(version, folder):
    expected = [f'PointGroupReducer-{version}-{target}.zip'
                for target in ('Windows-x64', 'macOS-arm64')]
    actual = sorted(p.name for p in folder.iterdir())
    assert actual == sorted(expected + [name + '.sha256' for name in expected]), actual
    sums = []
    for name in expected:
        package = folder / name
        digest = hashlib.sha256(package.read_bytes()).hexdigest()
        checksum = (folder / (name + '.sha256')).read_text().split()
        assert checksum == [digest, name], f'Checksum mismatch: {name}'
        with zipfile.ZipFile(package) as archive:
            bad = archive.testzip()
            assert bad is None, f'Corrupt ZIP entry: {bad}'
            info_names = [n for n in archive.namelist() if n.endswith('/BUILD-INFO.json')]
            assert len(info_names) == 1, info_names
            info = json.loads(archive.read(info_names[0]))
            assert info['version'] == version
            assert info['architecture'] == ('arm64' if 'macOS' in name else 'x64')
            for field in ('source_tests', 'native_gui_smoke', 'native_cli_smoke',
                          'mathtext_and_three_language_smoke'):
                assert info[field] == 'passed', (name, field)
        sums.append(f'{digest}  {name}\n')
    checksums = folder / 'SHA256SUMS.txt'
    checksums.write_text(''.join(sums), encoding='utf-8')
    return [folder / name for name in expected] + [checksums]


def obsolete_asset(name):
    return bool(re.fullmatch(
        r'PointGroupReducer-[0-9.]+-(macOS-x64|macOS-Intel|macOS-BuildKit|GitHub-Source)\.zip(?:\.sha256)?',
        name))


def clean_obsolete_assets(repo, current_tag):
    # Preserve historical Windows/Apple Silicon packages for rollback.
    removed = []
    page = 1
    while True:
        releases = api(f'repos/{repo}/releases?per_page=100&page={page}')
        for release in releases:
            if release['tag_name'] == current_tag or release['draft']:
                continue
            for asset in release['assets']:
                if obsolete_asset(asset['name']):
                    gh('api', '--method', 'DELETE', f"repos/{repo}/releases/assets/{asset['id']}")
                    removed.append({'tag': release['tag_name'], 'name': asset['name']})
            body = release['body'] or ''
            body = '\n'.join(line for line in body.split('\n')
                             if not line.startswith('| Intel Mac |'))
            body = body.replace('Windows x64, Apple Silicon and Intel Mac standalone packages',
                                'Windows x64 and Apple Silicon standalone packages')
            if release['tag_name'] == 'v2.2.0':
                body = ('Historical v2.2.0 Windows package. The retired macOS BuildKit and '
                        'duplicate source archive have been removed. Use the latest release '
                        'for Windows x64 or Apple Silicon macOS. Source remains available '
                        'through the tag and GitHub source downloads.\n\n'
                        '历史 Windows 版本；旧 macOS BuildKit 与重复源码附件已删除。'
                        '请优先使用最新 Windows 或 Apple 芯片 Mac 软件包。')
            if body != release['body']:
                gh('api', '--method', 'PATCH', f"repos/{repo}/releases/{release['id']}",
                   '-f', 'body=' + body)
        if len(releases) < 100:
            break
        page += 1
    # Gather pages before deleting, avoiding pagination shifts.
    intel_artifacts = []
    page = 1
    while True:
        result = api(f'repos/{repo}/actions/artifacts?per_page=100&page={page}')
        for artifact in result['artifacts']:
            if artifact['name'] in ('macOS-Intel', 'QA-macOS-Intel'):
                intel_artifacts.append(artifact)
        if len(result['artifacts']) < 100:
            break
        page += 1
    for artifact in intel_artifacts:
        gh('api', '--method', 'DELETE', f"repos/{repo}/actions/artifacts/{artifact['id']}")
    return {'release_assets': removed,
            'intel_workflow_artifacts': [a['id'] for a in intel_artifacts]}


def main():
    repo = os.environ['GH_REPO']
    assert repo == 'lightzfpwings/pointgroup-reducer', repo
    version = (ROOT / 'VERSION').read_text().strip()
    assert re.fullmatch(r'\d+\.\d+\.\d+', version), version
    tag = 'v' + version
    ref = os.environ['RELEASE_REF']
    if ref.startswith('refs/tags/'):
        assert ref == 'refs/tags/' + tag, 'Tag must match VERSION'
    sha = os.environ['GITHUB_SHA']
    assets = package_checks(version, ROOT / 'release-assets')
    tags = api(f'repos/{repo}/git/matching-refs/tags/{tag}')
    matching = [t for t in tags if t['ref'] == 'refs/tags/' + tag]
    if matching:
        obj = matching[0]['object']
        if obj['type'] == 'tag':
            obj = api(f"repos/{repo}/git/tags/{obj['sha']}")['object']
        assert obj['type'] == 'commit' and obj['sha'] == sha, 'Existing tag has different source'
    releases = api(f'repos/{repo}/releases?per_page=100')
    release = next((r for r in releases if r['tag_name'] == tag), None)
    if release is None:
        gh('release', 'create', tag, '--draft', '--target', sha,
           '--title', f'Point Group Reducer {tag}', '--notes-file', str(ROOT / 'RELEASE_NOTES.md'))
        releases = api(f'repos/{repo}/releases?per_page=100')
        release = next(r for r in releases if r['tag_name'] == tag)
    assert release['target_commitish'] == sha, 'Release has different source'
    release_path = f"repos/{repo}/releases/{release['id']}"
    gh('release', 'upload', tag, *[str(p) for p in assets], '--clobber')
    release = api(release_path)
    expected = {p.name: p for p in assets}
    for asset in release['assets']:
        if asset['name'] not in expected:
            gh('api', '--method', 'DELETE', f"repos/{repo}/releases/assets/{asset['id']}")
    release = api(release_path)
    assert {a['name'] for a in release['assets']} == set(expected)
    for asset in release['assets']:
        path = expected[asset['name']]
        assert asset['state'] == 'uploaded' and asset['size'] == path.stat().st_size
        assert asset['digest'] == 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
    gh('release', 'edit', tag, '--draft=false', '--prerelease=false', '--latest',
       '--notes-file', str(ROOT / 'RELEASE_NOTES.md'))
    result = clean_obsolete_assets(repo, tag)
    result['release'] = api(f'repos/{repo}/releases/tags/{tag}')['html_url']
    (ROOT / 'release-assets' / 'PUBLISH-REPORT.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
