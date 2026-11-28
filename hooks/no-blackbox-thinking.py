#!/usr/bin/env python3
"""Inject a reminder and the last recorded agy context estimate."""
import json
from pathlib import Path
import sqlite3
import sys
import uuid

REMINDER = 'EFFORT_LEVEL: 0. think: off. ⚠️一旦掉进了“think”标签就尽最大努力输出“/think”的xml标签，加油！'


def fields(data):
    def varint(pos):
        value = 0
        for shift in range(0, 70, 7):
            byte = data[pos]
            pos += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, pos
        raise ValueError('Invalid varint')
    pos = 0
    while pos < len(data):
        tag, pos = varint(pos)
        wire = tag & 7
        if wire == 0:
            value, pos = varint(pos)
        elif wire == 2:
            size, pos = varint(pos)
            end = pos + size
            if end > len(data):
                raise ValueError('Truncated field')
            value, pos = data[pos:end], end
        elif wire in (1, 5):
            size = 8 if wire == 1 else 4
            value, pos = data[pos:pos + size], pos + size
        else:
            raise ValueError('Unsupported wire type')
        yield tag >> 3, wire, value


def get(data, number, wire):
    return next(value for field, kind, value in fields(data)
                if field == number and kind == wire)


def context_note(payload):
    try:
        cid = str(uuid.UUID(payload['conversationId']))
        path = Path.home() / '.gemini/antigravity-cli/conversations' / (cid + '.db')
        with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=0.1) as db:
            rows = db.execute('SELECT data FROM gen_metadata ORDER BY idx DESC LIMIT 10')
            for (data,) in rows:
                try:
                    window = get(get(get(data, 1, 2), 9, 2), 10, 2)
                    used, limit = get(window, 1, 0), get(window, 4, 0)
                    if not 0 <= used < 100_000_000 or not 0 < limit < 100_000_000:
                        continue
                    return f'（当前上下文使用 {used / 1000:.1f}K / {limit / 1000:.1f}K，{used / limit:.1%}）'
                except (ValueError, IndexError, StopIteration, TypeError):
                    continue
    except (KeyError, ValueError, TypeError, sqlite3.Error, OSError):
        pass
    return ''


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            payload = {}
    except (ValueError, OSError):
        payload = {}
    note = context_note(payload)
    message = f'{note}{REMINDER}' if note else REMINDER
    print(json.dumps({'injectSteps': [{'systemMessage': {'systemMessage': message}}]},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
