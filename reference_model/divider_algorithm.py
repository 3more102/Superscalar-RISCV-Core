#!/usr/bin/env python3
"""Bit-accurate model of rtl/mdu/div_unit.sv restoring algorithm."""
MASK=0xffffffff

def u32(x): return x&MASK
def s32(x):
    x&=MASK
    return x-(1<<32) if x&(1<<31) else x

def abs32(v):
    v&=MASK
    return u32(-s32(v)) if v&(1<<31) else v

def restoring(a,b,op,latency=8):
    assert latency>0 and 32%latency==0
    if b==0:
        return MASK if op in ('div','divu') else u32(a)
    if op in ('div','rem') and u32(a)==0x80000000 and u32(b)==MASK:
        return 0x80000000 if op=='div' else 0
    signed=op in ('div','rem')
    q=abs32(a) if signed else u32(a)
    d=abs32(b) if signed else u32(b)
    rem=0
    steps=32//latency
    for _cyc in range(latency):
        for _ in range(steps):
            rem=((rem&0xffffffff)<<1)|((q>>31)&1)
            q=(q<<1)&MASK
            if rem>=d:
                rem-=d; q|=1
    if signed and ((u32(a)>>31) ^ (u32(b)>>31)):
        q=u32(-q)
    if signed and (u32(a)>>31):
        rem=u32(-rem)
    return q if op in ('div','divu') else u32(rem)
