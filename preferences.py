"""Remember the UI language; preference failures must not block startup."""
import json
import os
from pathlib import Path
import sys
from i18n import LANGUAGES


def settings_path():
    if os.environ.get('POINTGROUP_SETTINGS_PATH'):
        return Path(os.environ['POINTGROUP_SETTINGS_PATH'])
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/PointGroupReducer/settings.json'
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'PointGroupReducer/settings.json'
    return Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'PointGroupReducer/settings.json'


def load_language():
    try:
        value = json.loads(settings_path().read_text(encoding='utf-8')).get('language')
        return value if value in LANGUAGES else 'zh-Hans'
    except (OSError, ValueError, TypeError, AttributeError):
        return 'zh-Hans'


def save_language(language):
    if language not in LANGUAGES:
        raise ValueError('Unsupported language')
    try:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'language': language}), encoding='utf-8')
        temporary.replace(path)
        return True
    except OSError:
        return False

