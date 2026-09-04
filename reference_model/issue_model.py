#!/usr/bin/env python3
"""Small issue-policy model used to quantify the baseline 2-wide pairing rules.
This is not an RTL timing result; it models only front-end pairing/replay behavior.
"""
from dataclasses import dataclass

@dataclass
class Meta:
    rs1:int=0; rs2:int=0; rd:int=0
    rs1_used:bool=False; rs2_used:bool=False; rd_write:bool=False
    lane1:bool=False; special:bool=False

def decode_meta(ins:int)->Meta:
    opc=ins&0x7f; rd=(ins>>7)&31; f3=(ins>>12)&7; rs1=(ins>>15)&31; rs2=(ins>>20)&31; f7=(ins>>25)&0x7f
    m=Meta(rs1=rs1,rs2=rs2,rd=rd)
    if opc in (0x37,0x17): m.rd_write=True; m.lane1=True
    elif opc==0x13: m.rs1_used=True; m.rd_write=True; m.lane1=True
    elif opc==0x33:
        m.rs1_used=m.rs2_used=m.rd_write=True
        if f7==0x01: m.special=True
        else: m.lane1=True
    elif opc==0x03: m.rs1_used=True; m.rd_write=True; m.special=True
    elif opc==0x23: m.rs1_used=m.rs2_used=True; m.special=True
    elif opc==0x63: m.rs1_used=m.rs2_used=True; m.special=True
    elif opc==0x6f: m.rd_write=True; m.special=True
    elif opc==0x67: m.rs1_used=True; m.rd_write=True; m.special=True
    elif opc==0x73: m.special=True
    else: m.special=True
    return m

def can_pair(i0:int,i1:int)->bool:
    a,b=decode_meta(i0),decode_meta(i1)
    if not a.lane1 or a.special or not b.lane1 or b.special: return False
    if a.rd_write and a.rd:
        if b.rs1_used and b.rs1==a.rd: return False
        if b.rs2_used and b.rs2==a.rd: return False
        if b.rd_write and b.rd and b.rd==a.rd: return False
    return True

def issue_cycles(words):
    i=0; cyc=0; dual=0; single=0
    while i<len(words):
        if i+1<len(words) and can_pair(words[i],words[i+1]): i+=2; dual+=1
        else: i+=1; single+=1
        cyc+=1
    return {'instructions':len(words),'issue_cycles':cyc,'dual_cycles':dual,'single_cycles':single,'issue_ipc':len(words)/cyc if cyc else 0.0}
