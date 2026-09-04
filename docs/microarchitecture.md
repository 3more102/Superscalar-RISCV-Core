# 2-Wide In-Order RV32IM Microarchitecture

## Scope

The baseline is a 32-bit, 2-wide, in-order-issue/in-order-retirement RISC-V core implementing the requested RV32I integer instructions and RV32M. RVC, privileged CSRs, MMU, caches, interrupts and out-of-order execution are intentionally outside the baseline.

## Pipeline

```text
               +-----------------------------+
next_fetch_pc -> two-word instruction fetch  |
               +---------------+-------------+
                               |
                    2-entry fetch/replay buffer
                       slot0(old) slot1(young)
                         |            |
                     Decoder 0     Decoder 1
                         +-----+------+
                               |
                  dependency / pairing rules
                               |
                    +----------+----------+
                    |                     |
                  EX lane0              EX lane1
             ALU/BR/LSU/MUL/DIV          ALU
                    |                     |
                    +----------+----------+
                               |
                             MEM
                     one data-memory port
                               |
                              WB
                               |
                       2-write-port RF
```

Pipeline state is explicit in `ex_pipe_t`, `mem_pipe_t`, and `wb_pipe_t`. Each entry carries its decoded instruction, PC/instruction identity and a valid bit.

## Fetch and replay

The front end keeps two ordered instructions. `next_fetch_pc` points to the first instruction not already buffered.

* both slots issue: consume two and refill two (`next_fetch_pc += 8`)
* only slot0 issues: old slot1 shifts to slot0 and exactly one new instruction is appended (`next_fetch_pc += 4`)
* slot0 stalls: the pair is held
* redirect: both buffered younger instructions are discarded and `next_fetch_pc` is set to the branch/jump target

This implements the required rule that slot1 is replayed rather than discarded when pairing fails.

## Dual-issue policy

The baseline deliberately restricts dual issue to two independent simple integer ALU instructions. Slot1 is the ALU-only lane. RAW and WAW dependencies inside the pair are rejected. Any branch, jump, memory operation, M-extension instruction, system instruction or illegal instruction in slot0 serializes the pair.

This policy is conservative but architecturally safe and makes the superscalar mechanism auditable.

## Forwarding

Operands are selected in decode/issue with newest-result priority:

```text
RF -> WB0/WB1 -> MEM0/MEM1 -> EX0/EX1
```

Later stages in the list override earlier/older matches. EX forwarding is permitted for ALU, MUL and link-address results. A load in EX is not yet available and creates a one-cycle load-use stall; its data becomes forwardable from MEM. DIV/REM blocks EX until the divider returns `done`.

## Branches and jumps

Prediction is static not-taken. Conditional branches resolve in lane0 EX. A taken branch, JAL or JALR asserts `redirect_valid` combinationally, suppresses younger issue in that cycle, clears the fetch buffer at the following edge, and restarts fetch at the target. JALR clears target bit 0.

A branch occupies slot0 alone, so there is no same-cycle lane1 side effect to cancel when the branch resolves.

## Memory

Only lane0 may execute a load/store and the baseline has one data-memory port. The effective address is `rs1 + immediate`. The external bus address is word-aligned; byte enables and shifted store data select bytes. Loads perform byte/half/word sign or zero extension.

Misaligned halfword/word access is detected and converted to an internal precise halt/trap indication. Misaligned memory operations do not assert the external memory write/read enable.

## M extension

MUL/MULH/MULHSU/MULHU are combinational synthesizable operations in lane0 EX. DIV/DIVU/REM/REMU use a **restoring iterative divider**. `DIV_LATENCY` defaults to 8; at that setting four radix-2 quotient iterations are unrolled per clock, completing 32 quotient steps across eight busy clocks. The supported parameter values are positive divisors of 32. The EX stage is held while the divider is active; older MEM/WB work drains normally. Special divide-by-zero and signed-overflow results use the same configured latency.

Handled division cases include divide-by-zero and signed `INT_MIN / -1` overflow semantics.

## Precise ordering

Slot0 is always older than slot1. Slot1 can issue only with slot0. Both lanes traverse the same EX/MEM/WB stage count, so their retirement order is deterministic. Pair WAW is prohibited. Serializing faults/system instructions issue alone and block younger instructions while in flight.

## Cycle examples

Independent pair:

```text
Cycle N:   IF  I0 I1
Cycle N+1: ID  I0 I1 -> pair accepted
Cycle N+2: EX  I0 I1 in parallel
Cycle N+3: MEM I0 I1
Cycle N+4: WB  I0 then I1 logically
```

RAW pair:

```text
I0: ADD x5,x1,x2
I1: SUB x6,x5,x3

Cycle N:   pair RAW detected; issue I0 only
Cycle N+1: old I1 is slot0; x5 can be forwarded from EX and I1 issues
```

Load-use:

```text
I0: LW  x5,0(x1)
I1: ADD x6,x5,x3

LW issues alone. On the next cycle ADD sees x5 owned by an EX load and stalls.
One cycle later load data is in MEM and is forwarded to ADD.
```

## Precise traps and IALIGN

The baseline has no RVC support, therefore instruction alignment is 32 bits (4 bytes). Taken branch/JAL/JALR targets are checked after JALR clears bit 0. A misaligned taken target raises `EXC_INSTR_MISALIGNED` at the source instruction; a not-taken branch does not perform the target alignment check architecturally.

Trap-producing instructions are lane0-only/serializing in the baseline issue policy. Once the trap reaches WB, `halted` suppresses issue, commit, register-file writes and data-memory reads/writes. Portable simulation assertions and the OSS formal block both check post-halt quiescence.
