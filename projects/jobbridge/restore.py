#!/usr/bin/env python3
"""Restore the reviewed JobBridge source snapshot; no dependencies or network."""
import base64, hashlib, io, lzma, tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
EXPECTED = '94c21ca4aa21718e15d905bdf7e703773647dcbe4e972a1216104b4e2a57e4fa'

def main():
    encoded = b''.join((ROOT / 'payload' / f'{i:02d}.b64').read_bytes() for i in range(8))
    if len(encoded) != 63128:
        raise ValueError('Incomplete source snapshot: wrong encoded length')
    archive = base64.b64decode(encoded, validate=True)
    if len(archive) != 47344 or hashlib.sha256(archive).hexdigest() != EXPECTED:
        raise ValueError('Source integrity check failed; no files written')
    decoder = lzma.LZMADecompressor()
    raw = decoder.decompress(archive, max_length=5_000_001)
    if len(raw) > 5_000_000 or not decoder.eof:
        raise ValueError('Archive exceeds permitted size')
    destination = ROOT / 'app'
    if destination.is_symlink():
        raise ValueError('Destination must not be a symbolic link')
    destination.mkdir(exist_ok=True)
    base = destination.resolve()
    pending = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as source:
        for member in source.getmembers():
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or not member.isfile():
                raise ValueError(f'Unsafe archive member: {member.name}')
            target = destination.joinpath(*name.parts)
            if not target.resolve().is_relative_to(base) or target.is_symlink():
                raise ValueError('Unsafe output path')
            content = source.extractfile(member).read()
            if target.exists() and target.read_bytes() != content:
                raise FileExistsError(f'Refusing to overwrite modified source: {target}')
            pending.append((target, content))
    if len(pending) != 24:
        raise ValueError('Wrong source file count')
    for target, content in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    print(f'Verified SHA256 {EXPECTED}; restored {len(pending)} files to {destination}')

if __name__ == '__main__':
    main()
