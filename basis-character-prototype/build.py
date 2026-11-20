"""Build standalone offline pages and a source archive."""
import base64
import hashlib
from html import escape, unescape
import json
from pathlib import Path
import re
import runpy
import zipfile

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
VERSION = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
PAGE_NAME = f"BasisCharacterPrototype-{VERSION}"
LANGUAGES = ("zh-Hans", "zh-Hant", "en")
CORE_SCRIPTS = (
    "engine.js", "reducer-catalog.js", "reducer-adapter.js",
    "reduction-catalog.js", "reduction-engine.js", "salc.js", "vibrations.js", "structure.js", "formula-models.js", "messages-data.js",
    "i18n.js", "math-format.js",
)
APP_SCRIPT = "app.js"
CORE_OPEN = "<script data-basis-core>"
STATIC_TEXT = re.compile(r'(<(?:span|option|title)\b[^>]*data-i18n="([^"]+)"[^>]*>)([^<]*)(</(?:span|option|title)>)')


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def script_tag(name):
    return f'<script src="{name}"></script>'


def inline_script(name):
    content = (ROOT / name).read_text(encoding="utf-8")
    if "</script" in content.lower():
        raise ValueError(f"Unsafe script terminator in {name}")
    return content


def build_html():
    """Write the page used by both desktop apps and by the offline fallback."""
    DIST.mkdir(exist_ok=True)
    runpy.run_path(str(ROOT / "localization" / "build.py"))
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    favicon = "packaging/icons/favicon.png"
    encoded_icon = base64.b64encode((ROOT / favicon).read_bytes()).decode("ascii")
    html = html.replace(f'href="{favicon}"', f'href="data:image/png;base64,{encoded_icon}"')
    core_tags = "\n".join(map(script_tag, CORE_SCRIPTS))
    app_tag = script_tag(APP_SCRIPT)
    if html.count(core_tags) != 1 or html.count(app_tag) != 1:
        raise ValueError("Unexpected script tags in index.html")
    core = "\n".join(map(inline_script, CORE_SCRIPTS))
    html = html.replace(core_tags, f"{CORE_OPEN}\n{core}\n</script>")
    html = html.replace(app_tag, f"<script>\n{inline_script(APP_SCRIPT)}\n</script>")
    target = DIST / f"{PAGE_NAME}.html"
    target.write_bytes(html.encode("utf-8"))
    return target


def language_pages(html):
    translations = {}
    for line in (ROOT / "localization" / "messages.tsv").read_text(encoding="utf-8").splitlines():
        if line:
            key, traditional, english = line.split("\t")
            translations[key] = {"zh-Hant": traditional, "en": english}

    def localize(match):
        values = translations.get(unescape(match[2]))
        return match[1] + escape(values[language]) + match[4] if values else match[0]

    for language in LANGUAGES:
        variant = html.replace('lang="zh-CN"', f'lang="{language}"')
        script = f"<script>window.BasisDefaultLanguage={json.dumps(language)};</script>"
        variant = variant.replace("<head>", f"<head>\n{script}", 1)
        if language != "zh-Hans":
            variant = STATIC_TEXT.sub(localize, variant)
        target = DIST / f"{PAGE_NAME}-{language}.html"
        target.write_bytes(variant.encode("utf-8"))
        yield target


def source_archive():
    files = [ROOT / name for name in (
        "index.html", *CORE_SCRIPTS, APP_SCRIPT, "build.py", "package.json",
        "README.md", "README.en.md", "README.zh-Hant.md", "SIGNING.md", "SPECTROSCOPY_DESIGN.md",
    )]
    for folder, pattern in (
        ("localization", "*.tsv"), ("localization", "*.py"),
        ("compatibility", "*.py"), ("examples", "*.json"), ("examples", "*.xyz"),
        ("tests", "*.test.js"), ("tests/fixtures", "*.json"),
    ):
        files.extend(sorted((ROOT / folder).glob(pattern)))
    packaging_types = {".py", ".swift", ".md", ".cs", ".csproj", ".js", ".json", ".manifest", ".ps1", ".java", ".xml", ".desktop", ".sh", ".svg", ".png", ".ico", ".icns"}
    files.extend(path for path in sorted((ROOT / "packaging").rglob("*"))
                 if path.is_file() and path.suffix in packaging_types
                 and not {"obj", "bin", "__pycache__"}.intersection(path.relative_to(ROOT).parts))
    archive = DIST / f"{PAGE_NAME}-source.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in files:
            output.write(path, f"basis-character-prototype/{path.relative_to(ROOT).as_posix()}")
    return archive


def main():
    bundle = build_html()
    paths = [bundle, *language_pages(bundle.read_text(encoding="utf-8")), source_archive()]
    manifest = {
        "version": VERSION, "reductionIntegrated": True, "languages": LANGUAGES,
        "files": [{"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
                  for path in paths],
    }
    report = json.dumps(manifest, ensure_ascii=False, indent=2)
    (DIST / "manifest.json").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
