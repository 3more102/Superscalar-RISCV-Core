#!/usr/bin/env python3
"""Architectural RV32IM reference model for the implemented educational core."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse, json

MASK32 = 0xFFFFFFFF


def u32(x: int) -> int: return x & MASK32

def s32(x: int) -> int:
    x &= MASK32
    return x - (1 << 32) if x & 0x80000000 else x

def sext(x: int, bits: int) -> int:
    x &= (1 << bits) - 1
    return x - (1 << bits) if x & (1 << (bits - 1)) else x

def trunc_div(a: int, b: int) -> int:
    assert b != 0
    q = abs(a) // abs(b)
    return -q if (a < 0) ^ (b < 0) else q

@dataclass
class Commit:
    pc: int
    instr: int
    rd_we: bool = False
    rd: int = 0
    rd_value: int = 0
    mem_write: bool = False
    mem_addr: int = 0
    mem_data: int = 0

class RV32IM:
    def __init__(self, words, mem_size=65536):
        self.regs = [0] * 32
        self.pc = 0
        # Harvard memory model to match the RTL: program words live in
        # instruction memory while data memory starts cleared.  Keeping these
        # separate prevents accidental reads of instruction bytes through the
        # load/store port.
        self.imem = [int(w) & MASK32 for w in words]
        self.mem = bytearray(mem_size)
        self.halted = False
        self.trap = None
        self.commits: list[Commit] = []

    def _load(self, addr, size, unsigned):
        if size == 2 and addr & 1:
            self._trap("load_misaligned"); return 0
        if size == 4 and addr & 3:
            self._trap("load_misaligned"); return 0
        raw = int.from_bytes(self.mem[addr:addr+size], "little")
        if unsigned: return raw
        return u32(sext(raw, size * 8))

    def _store(self, addr, size, value):
        if size == 2 and addr & 1:
            self._trap("store_misaligned"); return False
        if size == 4 and addr & 3:
            self._trap("store_misaligned"); return False
        self.mem[addr:addr+size] = int(value & ((1 << (size*8))-1)).to_bytes(size, "little")
        return True

    def _trap(self, cause):
        self.trap = cause
        self.halted = True

    def fetch(self):
        # The SV memory model fills unused instruction words with EBREAK.
        # Instruction accesses are 32-bit aligned in this baseline.
        if self.pc & 0x3:
            self._trap("instruction_misaligned")
            return 0
        idx = self.pc >> 2
        if 0 <= idx < len(self.imem):
            return self.imem[idx]
        return 0x00100073

    def step(self):
        if self.halted: return None
        pc = self.pc
        ins = self.fetch()
        if self.halted:
            return None
        opc = ins & 0x7F
        rd = (ins >> 7) & 31
        f3 = (ins >> 12) & 7
        rs1 = (ins >> 15) & 31
        rs2 = (ins >> 20) & 31
        f7 = (ins >> 25) & 0x7F
        a, b = self.regs[rs1], self.regs[rs2]
        next_pc = u32(pc + 4)
        c = Commit(pc=pc, instr=ins)
        value = None

        if opc == 0x37: # LUI
            value = ins & 0xFFFFF000
        elif opc == 0x17: # AUIPC
            value = u32(pc + (ins & 0xFFFFF000))
        elif opc == 0x6F: # JAL
            imm = sext((((ins >> 31)&1)<<20) | (((ins>>12)&0xFF)<<12) | (((ins>>20)&1)<<11) | (((ins>>21)&0x3FF)<<1), 21)
            target = u32(pc + imm)
            if target & 0x3: self._trap("instruction_misaligned")
            else: value = u32(pc + 4); next_pc = target
        elif opc == 0x67 and f3 == 0: # JALR
            imm = sext(ins >> 20, 12)
            target = u32((a + imm) & ~1)
            if target & 0x3: self._trap("instruction_misaligned")
            else: value = u32(pc + 4); next_pc = target
        elif opc == 0x63:
            imm = sext((((ins>>31)&1)<<12) | (((ins>>7)&1)<<11) | (((ins>>25)&0x3F)<<5) | (((ins>>8)&0xF)<<1), 13)
            cond = {0:a==b, 1:a!=b, 4:s32(a)<s32(b), 5:s32(a)>=s32(b), 6:a<b, 7:a>=b}.get(f3)
            if cond is None: self._trap("illegal")
            elif cond:
                target = u32(pc + imm)
                if target & 0x3: self._trap("instruction_misaligned")
                else: next_pc = target
        elif opc == 0x03:
            imm = sext(ins >> 20, 12); addr = u32(a + imm)
            spec = {0:(1,False),1:(2,False),2:(4,False),4:(1,True),5:(2,True)}.get(f3)
            if spec is None: self._trap("illegal")
            else: value = self._load(addr, *spec)
        elif opc == 0x23:
            imm = sext(((ins >> 25) << 5) | ((ins >> 7) & 0x1F), 12); addr = u32(a + imm)
            size = {0:1,1:2,2:4}.get(f3)
            if size is None: self._trap("illegal")
            elif self._store(addr, size, b):
                c.mem_write=True; c.mem_addr=addr; c.mem_data=b
        elif opc == 0x13:
            imm = sext(ins >> 20, 12)
            if f3 == 0: value = u32(a + imm)
            elif f3 == 2: value = int(s32(a) < imm)
            elif f3 == 3: value = int(a < u32(imm))
            elif f3 == 4: value = a ^ u32(imm)
            elif f3 == 6: value = a | u32(imm)
            elif f3 == 7: value = a & u32(imm)
            elif f3 == 1 and f7 == 0: value = u32(a << ((ins>>20)&31))
            elif f3 == 5 and f7 == 0: value = a >> ((ins>>20)&31)
            elif f3 == 5 and f7 == 0x20: value = u32(s32(a) >> ((ins>>20)&31))
            else: self._trap("illegal")
        elif opc == 0x33:
            sh = b & 31
            if f7 == 0x01:
                if f3 == 0: value = u32(a * b)
                elif f3 == 1: value = ((s32(a) * s32(b)) & 0xFFFFFFFFFFFFFFFF) >> 32
                elif f3 == 2: value = ((s32(a) * b) & 0xFFFFFFFFFFFFFFFF) >> 32
                elif f3 == 3: value = ((a * b) >> 32) & MASK32
                elif f3 == 4:
                    if b == 0: value = MASK32
                    elif a == 0x80000000 and b == MASK32: value = 0x80000000
                    else: value = u32(trunc_div(s32(a), s32(b)))
                elif f3 == 5: value = MASK32 if b == 0 else a // b
                elif f3 == 6:
                    if b == 0: value = a
                    elif a == 0x80000000 and b == MASK32: value = 0
                    else:
                        q=trunc_div(s32(a),s32(b)); value=u32(s32(a)-q*s32(b))
                elif f3 == 7: value = a if b == 0 else a % b
                else: self._trap("illegal")
            elif f7 == 0x00:
                table={0:u32(a+b),1:u32(a<<sh),2:int(s32(a)<s32(b)),3:int(a<b),4:a^b,5:a>>sh,6:a|b,7:a&b}
                value=table.get(f3)
                if value is None: self._trap("illegal")
            elif f7 == 0x20 and f3 == 0: value=u32(a-b)
            elif f7 == 0x20 and f3 == 5: value=u32(s32(a)>>sh)
            else: self._trap("illegal")
        elif opc == 0x73:
            if ins == 0x00100073: self._trap("breakpoint")
            elif ins == 0x00000073: self._trap("ecall")
            else: self._trap("illegal")
        else:
            self._trap("illegal")

        if self.halted:
            return None
        if value is not None:
            if rd != 0:
                self.regs[rd] = u32(value)
            c.rd_we = rd != 0; c.rd = rd; c.rd_value = u32(value)
        self.regs[0] = 0
        self.pc = next_pc
        self.commits.append(c)
        return c

    def run(self, max_steps=100000):
        for _ in range(max_steps):
            if self.halted: break
            self.step()
        if not self.halted:
            raise RuntimeError(f"reference model did not halt within {max_steps} steps")
        return self


def load_hex(path):
    words=[]
    for line in Path(path).read_text().splitlines():
        line=line.strip().split('#')[0]
        if line: words.append(int(line,16))
    return words


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('hex'); ap.add_argument('--json')
    args=ap.parse_args(); m=RV32IM(load_hex(args.hex)).run()
    out={"trap":m.trap,"pc":m.pc,"regs":[f"0x{x:08x}" for x in m.regs],"commits":[asdict(c) for c in m.commits]}
    if args.json: Path(args.json).write_text(json.dumps(out,indent=2))
    else: print(json.dumps(out,indent=2))

if __name__=='__main__': main()
