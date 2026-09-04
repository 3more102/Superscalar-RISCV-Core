# Formal verification

The default open-source formal flow uses **yosys-slang + SymbiYosys**.

Targets:

- `issue.sby` — exhaustive combinational proof of dual-issue ordering / RAW / WAW / structural blocking rules.
- `alu_branch.sby` — exhaustive ALU and branch truth-function checks over symbolic operands.
- `core.sby` — bounded core invariants (x0, retirement ordering, halt quiescence, memory-port exclusivity, divider stall, EX→MEM PC association).

Core properties are immediate assertions under `` `ifdef FORMAL `` inside `rtl/core/superscalar_core.sv`. This intentionally avoids `bind`/rich SVA dependence in the default OSS flow.

Run:

```bash
python3 scripts/run_formal.py
# or
make formal
```

A result is reported as PASS only when `sby` actually executes all three targets successfully.
