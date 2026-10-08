"""Bundle the offline UI and a source ZIP. Python standard library only."""
from pathlib import Path
import hashlib
import json
import zipfile
import runpy
from html.parser import HTMLParser
import html as html_tools

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
VERSION = json.loads((ROOT / "package.json").read_text())["version"]
runpy.run_path(str(ROOT / "localization" / "build.py"))
html = (ROOT / "index.html").read_text(encoding="utf-8")
scripts=("engine.js", "reducer-catalog.js", "reducer-adapter.js", "reduction-catalog.js", "reduction-engine.js", "messages-data.js", "i18n.js", "math-format.js", "app.js")
for name in scripts:
    content = (ROOT / name).read_text(encoding="utf-8")
    if "</script" in content.lower():
        raise ValueError("Unsafe script terminator in " + name)
    html = html.replace('<script src="' + name + '"></script>', '<script>\n' + content + '\n</script>')
bundle = DIST / f"BasisCharacterPrototype-{VERSION}.html"
bundle.write_text(html, encoding="utf-8")
messages={line.split('\t')[0]:line.split('\t')[1:] for line in (ROOT/'localization/messages.tsv').read_text(encoding='utf-8').splitlines() if line}
variants=[]
for language in ("zh-Hans", "zh-Hant", "en"):
    # 初始正文及默认语言一并设置；运行时仍能切换并记住用户偏好。
    column=None if language=='zh-Hans' else 0 if language=='zh-Hant' else 1
    variant=html.replace('lang="zh-CN"',f'lang="{language}"').replace('<head>','<head>\n<script>window.BasisDefaultLanguage='+json.dumps(language)+';</script>')
    if column is not None:
        import re
        def translated(match):
            key=html_tools.unescape(match.group(2));return match.group(1)+html_tools.escape(messages[key][column])+match.group(4) if key in messages else match.group(0)
        variant=re.sub(r'(<(?:span|option|title)\b[^>]*data-i18n="([^"]+)"[^>]*>)([^<]*)(</(?:span|option|title)>)',translated,variant)
    target=DIST/f"BasisCharacterPrototype-{VERSION}-{language}.html"
    target.write_text(variant,encoding='utf-8');variants.append(target)
files = ["index.html", *scripts, "build.py", "README.md", "README.en.md", "README.zh-Hant.md", "package.json"]
files += [str(path.relative_to(ROOT)) for path in sorted((ROOT/'localization').glob('*')) if path.is_file()]
files += [str(path.relative_to(ROOT)) for path in sorted((ROOT / "compatibility").glob("*")) if path.is_file()]
files += [str(path.relative_to(ROOT)) for path in sorted((ROOT / "tests").glob("*.test.js"))]
files += [str(path.relative_to(ROOT)) for path in sorted((ROOT / "tests").rglob("*.json"))]
files += [str(path.relative_to(ROOT)) for path in sorted((ROOT / "packaging").rglob("*")) if path.is_file() and not any(part in ("obj", "bin") for part in path.parts) and path.suffix in (".py", ".swift", ".md", ".cs", ".csproj", ".js", ".json", ".manifest", ".ps1")]
archive = DIST / f"BasisCharacterPrototype-{VERSION}-source.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as out:
    for name in files:
        out.write(ROOT / name, "basis-character-prototype/" + name)
    out.write(bundle, "basis-character-prototype/" + bundle.name)
    for path in variants:out.write(path,"basis-character-prototype/"+path.name)
    for path in sorted((ROOT / "examples").glob("*.json")):
        out.write(path, "basis-character-prototype/examples/" + path.name)
    for path in sorted((ROOT / "validation").glob("*")):
        if path.is_file():
            out.write(path, "basis-character-prototype/validation/" + path.name)
manifest = {"version": VERSION, "reductionIntegrated": True, "languages": ["zh-Hans","zh-Hant","en"], "files": []}
for path in (bundle, *variants, archive):
    manifest["files"].append({"name": path.name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
(DIST / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
