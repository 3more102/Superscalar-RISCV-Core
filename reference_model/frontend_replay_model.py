#!/usr/bin/env python3
"""Executable model of the RTL two-entry front-end/replay queue.

It models only valid bits/PC movement, not instruction semantics.  Its purpose is
to stress the baseline rule: when slot0 issues alone, old slot1 becomes the next
slot0 and must never be lost or duplicated.
"""
from dataclasses import dataclass

MASK32=0xffffffff

@dataclass
class Frontend:
    reset_pc:int=0
    buf_v0:bool=False
    buf_v1:bool=False
    buf_pc0:int=0
    buf_pc1:int=0
    next_fetch_pc:int=0

    def __post_init__(self):
        self.next_fetch_pc=self.reset_pc & MASK32

    def step(self, issue0:bool=False, issue1:bool=False, redirect:int|None=None, halted:bool=False):
        issued=[]
        if redirect is not None:
            # RTL stalls issue whenever redirect_valid is asserted.
            if issue0 or issue1:
                raise ValueError('issue cannot coexist with redirect')
            self.buf_v0=self.buf_v1=False
            self.next_fetch_pc=redirect & MASK32
            return issued
        if halted:
            if issue0 or issue1:
                raise ValueError('issue cannot occur while halted')
            return issued
        if issue1 and not issue0:
            raise ValueError('slot1 cannot issue alone')
        if issue0 and not self.buf_v0:
            raise ValueError('slot0 issue from invalid buffer')
        if issue1 and not self.buf_v1:
            raise ValueError('slot1 issue from invalid buffer')

        if issue0:
            issued.append(self.buf_pc0)
        if issue1:
            issued.append(self.buf_pc1)

        if not self.buf_v0:
            self.buf_v0=self.buf_v1=True
            self.buf_pc0=self.next_fetch_pc
            self.buf_pc1=(self.next_fetch_pc+4)&MASK32
            self.next_fetch_pc=(self.next_fetch_pc+8)&MASK32
        elif issue0 and issue1:
            self.buf_v0=self.buf_v1=True
            self.buf_pc0=self.next_fetch_pc
            self.buf_pc1=(self.next_fetch_pc+4)&MASK32
            self.next_fetch_pc=(self.next_fetch_pc+8)&MASK32
        elif issue0:
            self.buf_v0=self.buf_v1
            self.buf_pc0=self.buf_pc1
            self.buf_v1=True
            self.buf_pc1=self.next_fetch_pc
            self.next_fetch_pc=(self.next_fetch_pc+4)&MASK32
        return issued

    def invariant(self):
        if self.buf_v1 and not self.buf_v0:
            return False
        if self.buf_v0 and self.buf_pc0 & 3:
            return False
        if self.buf_v1 and (self.buf_pc1 != ((self.buf_pc0+4)&MASK32)):
            return False
        return (self.next_fetch_pc & 3)==0
