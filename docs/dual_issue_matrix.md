# Baseline Dual-Issue Matrix

The implemented baseline uses lane0 as the full-featured lane and lane1 as a simple integer-ALU lane.

| Slot0 | Slot1 | Dual issue | Conditions / reason |
|---|---|---:|---|
| Integer ALU / OP-IMM | Integer ALU / OP-IMM | YES | No pair RAW, no pair WAW, no external load-use stall |
| LUI/AUIPC | integer ALU | YES | Same dependency rules |
| integer ALU | LUI/AUIPC | YES | Same dependency rules |
| ALU | LOAD/STORE | NO | lane1 has no memory path |
| LOAD/STORE | ALU | NO | baseline treats lane0 memory op as structural serializer |
| LOAD | LOAD | NO | one memory port |
| STORE | STORE | NO | one memory port |
| LOAD | STORE | NO | one memory port |
| branch | anything | NO | control-flow serialization |
| JAL/JALR | anything | NO | redirect serialization |
| MUL/DIV/REM | anything | NO | M unit is lane0-only in baseline |
| anything | MUL/DIV/REM | NO | lane1 has no M unit |
| ECALL/EBREAK | anything | NO | serializing termination/trap |
| illegal | anything | NO | precise trap behavior |

Pair hazards:

* RAW: slot1 source equals slot0 nonzero destination -> slot1 replayed.
* WAW: both slots write the same nonzero destination -> slot1 replayed.
* WAR does not block because operands are read before either instruction writes back and execution/retirement is in order.
