"""Exercise the installed Debian package and its offline UI on a Linux desktop runner."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
VERSION = json.loads((ROOT / "package.json").read_text())["version"]
PACKAGE = DIST / f"BasisCharacter-{VERSION}-Linux-all.deb"
INSTALLED = Path("/usr/share/basis-character/index.html")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def launch_target(work):
    # Exercise the real launcher and xdg-open. In a headless session the BROWSER
    # preference captures the URL handed to the graphical browser tested below.
    updater = Path("/usr/share/applications/basis-character-update.desktop")
    subprocess.run(["desktop-file-validate", updater], check=True)
    handler = subprocess.check_output(["xdg-mime","query","default","x-scheme-handler/basis-character-update"],text=True).strip()
    assert handler == updater.name, handler
    capture = work / "browser-argument"
    handler = work / "record-browser"
    handler.write_text('#!/bin/sh\nprintf "%s\\n" "$1" > "$BASIS_LAUNCH_CAPTURE"\n')
    handler.chmod(0o755)
    env = dict(os.environ, BROWSER=str(handler), BASIS_LAUNCH_CAPTURE=str(capture))
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "DESKTOP_SESSION",
                "KDE_FULL_SESSION", "GNOME_DESKTOP_SESSION_ID"):
        env.pop(key, None)
    subprocess.run(["/usr/bin/basis-character"], env=env, check=True, timeout=30)
    target = capture.read_text().strip()
    assert target in (str(INSTALLED), INSTALLED.as_uri()), target
    return INSTALLED.as_uri()


def check_browser(work, uri):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_experimental_option("prefs", {
        "download.default_directory": str(work),
        "download.prompt_for_download": False,
    })
    executable = shutil.which("chromedriver")
    if not executable:
        executable = str(Path(os.environ["CHROMEWEBDRIVER"]) / "chromedriver")
    with webdriver.Chrome(service=Service(executable_path=executable), options=options) as browser:
        wait = WebDriverWait(browser, 30)
        browser.execute_cdp_cmd("Network.enable", {})
        browser.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": True, "latency": 0, "downloadThroughput": 0, "uploadThroughput": 0,
        })
        browser.get(uri)

        def field(name):
            return browser.find_element(By.ID, name)

        def downloaded(name):
            path = work / name
            wait.until(lambda _: path.is_file() and path.stat().st_size > 0)
            return path

        Select(field("language")).select_by_value("en")
        template = browser.find_element(By.CSS_SELECTOR, 'button[data-template="water"]')
        template.find_element(By.XPATH, "ancestor::details/summary").click()
        template.click()
        field("save-project").click()
        project = downloaded("symmetry-input-C2v.json")
        input_data = json.loads(project.read_text())
        assert input_data["input"]["group"] == "C2v"
        assert len(input_data["input"]["sites"]) == 3

        field("new-project").click()
        field("project-file").send_keys(str(project))
        wait.until(lambda _: field("site-count").text.startswith("3 "))
        field("calculate").click()
        wait.until(lambda _: field("calculate-salc").is_displayed())
        field("calculate-salc").click()
        wait.until(lambda _: field("salc-table").is_displayed())
        field("export-result").click()
        result = json.loads(downloaded("symmetry-result-C2v.json").read_text())
        assert result["input"] == input_data["input"]
        assert result["engineVersion"] == VERSION
        spaces = {s["irrep"]: s for s in result["salc"]["spaces"]}
        assert set(spaces) == {"A1", "B1"}
        for irrep, sign in (("A1", 1), ("B1", -1)):
            a, b = spaces[irrep]["copies"][0]["vectors"][0]["coefficients"]
            assert math.isclose(a * a, .5, abs_tol=1e-8) and math.isclose(a * b, sign * .5, abs_tol=1e-8)

        browser.find_element(By.CSS_SELECTOR, "#copy-card > summary").click()
        field("copy-text").click()
        expected = field("copy-content").get_attribute("value")
        assert "SALC A1" in expected
        # A browser may require keyboard copying of the app-selected text.
        wait.until(lambda _: "cop" in field("status").text.lower())
        copy_method = "clipboard"
        if "select" in field("status").text.lower():
            field("copy-content").send_keys(Keys.CONTROL, "c")
            copy_method = "selected text"
        Select(field("workflow")).select_by_value("manual")
        field("manual-characters").clear()
        field("manual-characters").send_keys(Keys.CONTROL, "v")
        wait.until(lambda _: field("manual-characters").get_attribute("value") == expected)
        Select(field("workflow")).select_by_value("vibrations")
        field("formula-text").send_keys("C2H6O")
        field("find-models").click()
        candidates = browser.find_elements(By.CSS_SELECTOR, "#formula-choices button")
        assert len(candidates) == 2
        candidates[1].click()
        assert Select(field("group")).first_selected_option.get_attribute("value") == "C2v"
        assert not field("calculate").is_enabled()
        field("confirm-structure").click()
        field("calculate").click()
        wait.until(lambda _: "IR allowed 17 · Raman allowed 21" in field("result-body").text)
        assert browser.execute_script("""
          return [...document.querySelectorAll('.activity-table th,.activity-table td')].every(cell =>
            getComputedStyle(cell).textAlign === 'center') &&
            parseFloat(getComputedStyle(document.body).paddingTop) >= 56 &&
            parseFloat(getComputedStyle(document.body).paddingBottom) >= 56;
        """)
        return {"browser": browser.capabilities["browserVersion"], "offline": True, "example": "C2v water",
                "salcIrreps": list(spaces), "projectRoundTrip": True, "clipboardRoundTrip": copy_method,
                "formulaModel":"dimethyl-ether", "irBands":17, "ramanBands":21}


def main():
    status = subprocess.check_output(
        ["dpkg-query", "-W", "-f=${Status} ${Version} ${Architecture}", "basis-character"], text=True)
    assert status == f"install ok installed {VERSION} all", status
    desktop = "/usr/share/applications/basis-character.desktop"
    subprocess.run(["desktop-file-validate", desktop], check=True)
    assert "Exec=basis-character\n" in Path(desktop).read_text()
    assert digest(INSTALLED) == digest(DIST / f"BasisCharacterPrototype-{VERSION}.html")
    with TemporaryDirectory(prefix="basis-linux-qa-") as temporary:
        work = Path(temporary)
        checked = check_browser(work, launch_target(work))
    report = {"status": "passed", "platform": "Linux", "version": VERSION, "architecture": "all",
              "packageSha256": digest(PACKAGE), "htmlSha256": digest(INSTALLED), "installed": True, **checked}
    text = json.dumps(report, indent=2) + "\n"
    (DIST / "linux-package-check.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
