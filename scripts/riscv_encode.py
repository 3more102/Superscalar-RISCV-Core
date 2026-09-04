#!/usr/bin/env python3
"""Small RV32IM encoder used when a RISC-V GCC toolchain is unavailable."""
from __future__ import annotations

MASK32 = 0xFFFFFFFF


def _check_reg(r: int) -> int:
    if not 0 <= r < 32:
        raise ValueError(f"register out of range: x{r}")
    return r


def r_type(f7, rs2, rs1, f3, rd, opc=0x33):
    return ((f7 & 0x7F) << 25) | (_check_reg(rs2) << 20) | (_check_reg(rs1) << 15) | ((f3 & 7) << 12) | (_check_reg(rd) << 7) | opc


def i_type(imm, rs1, f3, rd, opc):
    return ((imm & 0xFFF) << 20) | (_check_reg(rs1) << 15) | ((f3 & 7) << 12) | (_check_reg(rd) << 7) | opc


def s_type(imm, rs2, rs1, f3, opc=0x23):
    u = imm & 0xFFF
    return ((u >> 5) << 25) | (_check_reg(rs2) << 20) | (_check_reg(rs1) << 15) | ((f3 & 7) << 12) | ((u & 0x1F) << 7) | opc


def b_type(imm, rs2, rs1, f3, opc=0x63):
    if imm & 1:
        raise ValueError("branch offset must be even")
    u = imm & 0x1FFF
    return (((u >> 12) & 1) << 31) | (((u >> 5) & 0x3F) << 25) | (_check_reg(rs2) << 20) | (_check_reg(rs1) << 15) | ((f3 & 7) << 12) | (((u >> 1) & 0xF) << 8) | (((u >> 11) & 1) << 7) | opc


def u_type(imm, rd, opc):
    return (imm & 0xFFFFF000) | (_check_reg(rd) << 7) | opc


def j_type(imm, rd, opc=0x6F):
    if imm & 1:
        raise ValueError("jump offset must be even")
    u = imm & 0x1FFFFF
    return (((u >> 20) & 1) << 31) | (((u >> 1) & 0x3FF) << 21) | (((u >> 11) & 1) << 20) | (((u >> 12) & 0xFF) << 12) | (_check_reg(rd) << 7) | opc


def addi(rd, rs1, imm): return i_type(imm, rs1, 0, rd, 0x13)
def slti(rd, rs1, imm): return i_type(imm, rs1, 2, rd, 0x13)
def sltiu(rd, rs1, imm): return i_type(imm, rs1, 3, rd, 0x13)
def xori(rd, rs1, imm): return i_type(imm, rs1, 4, rd, 0x13)
def ori(rd, rs1, imm): return i_type(imm, rs1, 6, rd, 0x13)
def andi(rd, rs1, imm): return i_type(imm, rs1, 7, rd, 0x13)
def slli(rd, rs1, sh): return i_type(sh & 31, rs1, 1, rd, 0x13)
def srli(rd, rs1, sh): return i_type(sh & 31, rs1, 5, rd, 0x13)
def srai(rd, rs1, sh): return i_type((0x20 << 5) | (sh & 31), rs1, 5, rd, 0x13)

def add(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 0, rd)
def sub(rd, rs1, rs2): return r_type(0x20, rs2, rs1, 0, rd)
def sll(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 1, rd)
def slt(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 2, rd)
def sltu(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 3, rd)
def xor(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 4, rd)
def srl(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 5, rd)
def sra(rd, rs1, rs2): return r_type(0x20, rs2, rs1, 5, rd)
def or_(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 6, rd)
def and_(rd, rs1, rs2): return r_type(0x00, rs2, rs1, 7, rd)

def lui(rd, imm): return u_type(imm, rd, 0x37)
def auipc(rd, imm): return u_type(imm, rd, 0x17)
def jal(rd, imm): return j_type(imm, rd)
def jalr(rd, rs1, imm): return i_type(imm, rs1, 0, rd, 0x67)

def beq(rs1, rs2, imm): return b_type(imm, rs2, rs1, 0)
def bne(rs1, rs2, imm): return b_type(imm, rs2, rs1, 1)
def blt(rs1, rs2, imm): return b_type(imm, rs2, rs1, 4)
def bge(rs1, rs2, imm): return b_type(imm, rs2, rs1, 5)
def bltu(rs1, rs2, imm): return b_type(imm, rs2, rs1, 6)
def bgeu(rs1, rs2, imm): return b_type(imm, rs2, rs1, 7)

def lb(rd, rs1, imm): return i_type(imm, rs1, 0, rd, 0x03)
def lh(rd, rs1, imm): return i_type(imm, rs1, 1, rd, 0x03)
def lw(rd, rs1, imm): return i_type(imm, rs1, 2, rd, 0x03)
def lbu(rd, rs1, imm): return i_type(imm, rs1, 4, rd, 0x03)
def lhu(rd, rs1, imm): return i_type(imm, rs1, 5, rd, 0x03)
def sb(rs2, rs1, imm): return s_type(imm, rs2, rs1, 0)
def sh(rs2, rs1, imm): return s_type(imm, rs2, rs1, 1)
def sw(rs2, rs1, imm): return s_type(imm, rs2, rs1, 2)

def mul(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 0, rd)
def mulh(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 1, rd)
def mulhsu(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 2, rd)
def mulhu(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 3, rd)
def div(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 4, rd)
def divu(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 5, rd)
def rem(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 6, rd)
def remu(rd, rs1, rs2): return r_type(0x01, rs2, rs1, 7, rd)

ECALL = 0x00000073
EBREAK = 0x00100073
NOP = 0x00000013


def write_hex(path, words):
    with open(path, "w", encoding="ascii") as f:
        for w in words:
            f.write(f"{w & MASK32:08x}\n")
