#!/usr/bin/env python3
"""Read-only A2WC0MME LAB v3 Subaru/Denso checksum auditor (no ROM writes)."""
from __future__ import annotations
import hashlib,struct,sys
from pathlib import Path
EXPECTED={
'v39':'43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4',
'v45':'92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329',
'v3':'def65da29d7a6c6387c186d7d8aeaf3cd36baa4a34d289807778cd9da47d538f'
}
TARGET=0x5AA5A55A
def inspect(data,label):
    if len(data)!=524288 or hashlib.sha256(data).hexdigest()!=EXPECTED[label]:
        raise ValueError(f'{label}: unexpected binary size or SHA-256')
    if data[0x2000:0x2008]!=b'A2WC0MME':raise ValueError('wrong ROM ID')
    assert struct.unpack_from('>II',data,0x7FB80)==(0x2000,0x7FAF7)
    assert all(struct.unpack_from('>III',data,0x7FB80+12*i)==(0,0,TARGET) for i in range(1,17))
    words=struct.iter_unpack('>I',data[0x2000:0x7FAF8])
    sum32=sum(w[0] for w in words)&0xffffffff
    stored=struct.unpack_from('>I',data,0x7FB88)[0]
    expected=(TARGET-sum32)&0xffffffff
    status='OK' if stored==expected else 'STALE'
    return status,sum32,stored,expected
if __name__=='__main__':
    if len(sys.argv)!=4:
        print('Usage: python verify_a2wc012e_v3_checksum.py ORIGINAL_V39.bin REFERENCE_V45.bin LAB_V3.bin')
        raise SystemExit(2)
    images={n:Path(p).read_bytes() for n,p in zip(EXPECTED,sys.argv[1:])}
    for n,b in images.items():
        status,sum32,stored,expected=inspect(b,n)
        print(f'{n}: {status}; sum=0x{sum32:08X}; stored=0x{stored:08X}; expected=0x{expected:08X}')
    assert inspect(images['v39'],'v39')[0]=='OK'
    assert inspect(images['v45'],'v45')[0]=='OK'
    assert inspect(images['v3'],'v3')[0]=='STALE'
    a,b=images['v39'],images['v3']
    changes=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    assert len(changes)==308
    assert all(0x6A612<=i<0x6A616 or 0x6AC40<=i<0x6AD84 for i in changes)
    # In-memory only, do NOT save to file:
    shadow=bytearray(b)
    shadow[0x7FB88:0x7FB8C]=inspect(b,'v3')[3].to_bytes(4,'big')
    assert (sum(w[0] for w in struct.iter_unpack('>I',shadow[0x2000:0x7FAF8]))+
            struct.unpack_from('>I',shadow,0x7FB88)[0]) & 0xFFFFFFFF == TARGET
    print('In-memory checksum adjustment verifies; no ROM output produced. NOT FOR FLASH.')
