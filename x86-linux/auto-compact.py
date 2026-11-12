#!/usr/bin/env python3
"""Toggle native checkpointing for the exact archived x86 build; restart required."""
from pathlib import Path
import argparse,hashlib,json,os,tempfile
p=argparse.ArgumentParser();p.add_argument('mode',choices=['on','off','status'],nargs='?',default='status');p.add_argument('--target',type=Path,default=Path.home()/'.local/bin/agy');a=p.parse_args()
m=json.loads((Path(__file__).resolve().parent/'agy-x86-patches.json').read_text());cfg=m['auto_compact'];t=a.target;b=t.read_bytes();sha=lambda x:hashlib.sha256(x).hexdigest();h=sha(b);states={m['patched_sha256']:'on',cfg['off_sha256']:'off'}
if h not in states:raise SystemExit('Unknown binary: refusing to modify '+h)
state=states[h]
if a.mode=='status' or a.mode==state:print('Auto compaction:',state);raise SystemExit
out=bytearray(b);o=int(cfg['offset'],16);assert out[o:o+7]==bytes.fromhex(cfg[state]);out[o:o+7]=bytes.fromhex(cfg[a.mode]);assert states[sha(out)]==a.mode
backup=Path.home()/'.local/share/agy-patches'/('agy-before-auto-compact-'+h+'.bak');backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():backup.write_bytes(b)
else:assert sha(backup.read_bytes())==h
fd,tmp=tempfile.mkstemp(prefix='agy-compact-',dir=t.parent)
try:
 with os.fdopen(fd,'wb') as f:f.write(out);f.flush();os.fsync(f.fileno())
 os.chmod(tmp,t.stat().st_mode & 0o777);os.replace(tmp,t)
finally:
 if os.path.exists(tmp):os.unlink(tmp)
print('Auto compaction:',a.mode,'— restart agy to apply.')
