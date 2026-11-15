#!/usr/bin/env python3
"""Install the agy reminder hook without replacing other named hooks."""
import json
from pathlib import Path
import shutil

root = Path.home() / '.gemini/config'
source = Path(__file__).with_name('no-blackbox-thinking.py')
target = root / 'hooks/no-blackbox-thinking.py'
config = root / 'hooks.json'
data = json.loads(config.read_text()) if config.exists() else {}
if not isinstance(data, dict):
    raise SystemExit('hooks.json must be a JSON object')
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, target)
data['no-blackbox-thinking'] = {'PreInvocation': [{
    'type': 'command', 'command': 'python3 "' + str(target) + '"', 'timeout': 5,
}]}
config.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print('Installed:', target)
print('Merged:', config)
print('Restart agy after first installation or hooks.json changes.')
