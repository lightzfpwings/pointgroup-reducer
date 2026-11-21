#!/usr/bin/python3 -I
"""Desktop protocol handler and fixed-purpose privileged DEB installation."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

REPO = "lightzfpwings/pointgroup-reducer"
VERSION = r"(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})"
HELPER = "/usr/lib/basis-character/update.py"
MESSAGES = {
    "progress": ("正在校验并安装更新…", "正在核對並安裝更新…", "Verifying and installing the update…"),
    "done": ("已更新。确定后重新打开应用。", "已更新。確定後重新開啟應用程式。", "Update installed. Select OK to reopen the app."),
    "error": ("更新未完成。请检查网络及安装权限后重试。", "更新未完成。請檢查網路與安裝權限後重試。", "Update did not finish. Check your network and installation permission, then retry."),
}

def parts(version):
    if not re.fullmatch(VERSION, version):
        raise ValueError("Invalid version")
    return tuple(map(int, version.split(".")))

def parse_link(link):
    u = urllib.parse.urlsplit(link)
    if u.scheme != "basis-character-update" or u.netloc != "install" or u.fragment:
        raise ValueError("Invalid update link")
    version = u.path.removeprefix("/")
    parts(version)
    language = urllib.parse.parse_qs(u.query).get("lang", ["en"])[0]
    return version, {"en": 2, "zh-Hant": 1, "zh-Hans": 0}.get(language, 2)

class ReleaseRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        if u.scheme != "https" or u.netloc not in {
            "github.com", "api.github.com", "objects.githubusercontent.com",
            "release-assets.githubusercontent.com", "github-releases.githubusercontent.com"
        }:
            raise ValueError("Unexpected GitHub redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def opened(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BasisCharacter-Updater"})
    return urllib.request.build_opener(ReleaseRedirects()).open(req, timeout=30)

def download(version, target, get=opened):
    parts(version)
    tag = "basis-v" + version
    name = f"BasisCharacter-{version}-Linux-all.deb"
    url = f"https://github.com/{REPO}/releases/download/{tag}/{name}"
    with get(f"https://api.github.com/repos/{REPO}/releases/tags/{tag}") as resp:
        data = resp.read(4*1024*1024 + 1)
    if len(data)>4*1024*1024:
        raise ValueError("Invalid release")
    release = json.loads(data)
    if release["tag_name"] != tag or release["draft"] is not False or release["prerelease"] is not False:
        raise ValueError("Not a stable release")
    asset, = [a for a in release["assets"] if a["name"] == name]
    if (asset["state"] != "uploaded" or asset["browser_download_url"] != url or
            not re.fullmatch(r"sha256:[0-9a-f]{64}", asset["digest"]) or not 0 < asset["size"] <= 256*1024*1024):
        raise ValueError("Invalid release asset")
    sha = hashlib.sha256()
    with get(url) as response, target.open("xb") as out:
        while chunk := response.read(131072):
            if out.tell() + len(chunk) > asset["size"]:
                raise ValueError("Invalid download size")
            out.write(chunk)
            sha.update(chunk)
    if target.stat().st_size != asset["size"] or "sha256:"+sha.hexdigest() != asset["digest"]:
        raise ValueError("Package checksum mismatch")

def install(version, get=opened):
    installed = subprocess.check_output(["/usr/bin/dpkg-query", "-W", "-f=${Version}", "basis-character"],text=True)
    if parts(version) <= parts(installed.strip()):
        raise ValueError("A newer version is already installed")
    # All bytes passed to dpkg are fetched and checked in a fresh root-owned directory.
    with tempfile.TemporaryDirectory(prefix="basis-update-", dir="/var/tmp") as tmp:
        deb = Path(tmp)/"update.deb"
        download(version, deb, get)
        for field, value in [("Package","basis-character"),("Version",version),("Architecture","all")]:
            actual = subprocess.check_output(["/usr/bin/dpkg-deb", "-f", deb, field],text=True).strip()
            if actual != value:
                raise ValueError("Unexpected Debian package identity")
        subprocess.run(["/usr/bin/dpkg", "--refuse-downgrade", "--install", deb], check=True)

def desktop(link):
    version, language = parse_link(link)
    progress = subprocess.Popen(["/usr/bin/zenity","--progress","--pulsate","--no-cancel","--auto-close",
                                 "--title=Basis Character","--text="+MESSAGES["progress"][language]],stdin=subprocess.PIPE)
    try:
        code = subprocess.run(["/usr/bin/pkexec", HELPER, "--install", version]).returncode
    finally:
        progress.communicate(b"100\n")
    if code == 126:
        return code
    kind = "done" if code==0 else "error"
    response = subprocess.run(["/usr/bin/zenity","--info" if code==0 else "--error","--title=Basis Character","--text="+MESSAGES[kind][language]])
    if code==0 and response.returncode==0:
        subprocess.Popen(["/usr/bin/basis-character"])
    return code

if __name__ == "__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--install" and os.geteuid()==0:
        install(sys.argv[2])
    elif len(sys.argv)==2 and os.geteuid()!=0:
        sys.exit(desktop(sys.argv[1]))
    else:
        sys.exit(2)
