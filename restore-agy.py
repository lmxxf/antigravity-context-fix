#!/usr/bin/env python3
"""Install the archived patched agy for Linux ARM64 or x86_64."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import tempfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def restore(arch, target):
    root = Path(__file__).resolve().parent
    folder, manifest, machine, elf_machine = {
        'arm': ('arm-linux', 'agy-patches.json', 'aarch64', 183),
        'x86': ('x86-linux', 'agy-x86-patches.json', 'x86_64', 62),
    }[arch]
    if platform.system() != 'Linux' or platform.machine() != machine:
        raise ValueError(f'{arch} archive requires Linux {machine}; current host is '
                         f'{platform.system()} {platform.machine()}')
    source = root / folder
    metadata = json.loads((source / manifest).read_text())
    expected = metadata['patched_sha256']
    data = gzip.decompress((source / 'agy.gz').read_bytes())
    if len(data) != metadata['size'] or sha256(data) != expected:
        raise ValueError('Archive size or SHA256 mismatch')
    if data[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', data, 18)[0] != elf_machine:
        raise ValueError('Archive ELF architecture mismatch')
    target = target.expanduser().absolute()
    if target.is_symlink():
        raise ValueError(f'Target is a symlink; specify its actual path with --target: {target}')
    if target.exists():
        old = sha256(target.read_bytes())
        if old == expected:
            print(f'Already installed: agy {metadata["version"]} ({arch})')
            return
        backup = Path.home() / '.local/share/agy-patches' / f'agy-before-restore-{old}.bak'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists():
            if sha256(backup.read_bytes()) != old:
                raise ValueError(f'Existing backup checksum mismatch: {backup}')
        else:
            shutil.copy2(target, backup)
            if sha256(backup.read_bytes()) != old:
                raise ValueError(f'Backup checksum mismatch: {backup}')
        print(f'Previous binary saved: {backup}')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='agy-restore-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, 0o755)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f'Restored agy {metadata["version"]} ({arch}): {target}')
    print('Restart agy. Use a new session to load complete rules.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arch', choices=('arm', 'x86'), help='arm = Linux ARM64; x86 = Linux x86_64')
    parser.add_argument('--target', type=Path, default=Path.home() / '.local/bin/agy',
                        help='installation path (default: ~/.local/bin/agy)')
    args = parser.parse_args()
    try:
        restore(args.arch, args.target)
    except (OSError, ValueError, KeyError, EOFError, struct.error) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
