# ISA Specification Sources

The instruction encodings and architectural semantics used by this project are based on the official RISC-V Ratified Specifications Library:

- RV32I Base Integer Instruction Set, Version 2.1: https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html
- M Extension for Integer Multiplication and Division, Version 2.0: https://docs.riscv.org/reference/isa/unpriv/m-st-ext.html

The M-extension implementation follows the specified divide-by-zero and signed-overflow results: quotient all ones and remainder equal to dividend for division by zero; `INT_MIN / -1` returns `INT_MIN` with zero remainder.

For the no-RVC baseline, the RV32I specification defines `IALIGN=32`: instructions are 4-byte aligned; instruction-address-misaligned is raised on a **taken** branch or unconditional jump whose target is not 4-byte aligned, and the exception is reported on the control-transfer instruction. A conditional branch that is not taken does not raise this exception. JALR forms its target by adding the sign-extended immediate to `rs1` and clearing target bit 0 before alignment is considered.
