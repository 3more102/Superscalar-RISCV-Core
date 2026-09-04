# Reference / Stimulus Functional Coverage

> This is executable architectural/stimulus coverage, **not RTL simulator code/functional coverage**.

Programs analyzed: **41**
Coverage points: **54/54**

## Branch outcome matrix

| Branch | Taken | Not taken |
|---|---:|---:|
| BEQ | 4 | 1 |
| BNE | 1 | 3 |
| BLT | 7 | 2 |
| BGE | 2 | 1 |
| BLTU | 1 | 3 |
| BGEU | 2 | 1 |

## Load/store types

Loads: LB=3, LH=2, LW=5, LBU=3, LHU=2

Stores: SB=6, SH=3, SW=6

Store byte-enable lanes: SB_lane0=2, SB_lane1=2, SB_lane2=1, SB_lane3=1, SH_lane0=1, SH_lane2=2

## M extension

MUL=5, MULH=3, MULHSU=3, MULHU=3, DIV=4, DIVU=3, REM=4, REMU=3

## Trap classes

instruction_misaligned=3, breakpoint=26, illegal=9, load_misaligned=1, store_misaligned=1, ecall=1

## Reserved illegal encodings

jalr_funct3=True, branch_funct3=True, load_funct3=True, store_funct3=True, shift_encoding=True, op_encoding=True, system=True

## Superscalar timing-model event stimuli

dual_issue=59, raw_block=42, waw_block=1, structural_block=119, load_use_stall=1, divider_stall=126, redirect_bubble=40

