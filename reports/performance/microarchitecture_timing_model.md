# Executable Microarchitecture Timing Model

**Important:** these are cycle-model results, not SystemVerilog simulation measurements.

| Program | Retired | Single cycles(model) | 2-wide cycles(model) | Speedup(model) | IPC(model) | Dual cycles | Load stalls | DIV stalls | Redirect bubbles |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01_alu | 23 | 28 | 17 | 1.647x | 1.353 | 11 | 0 | 0 | 0 |
| 02_dual_issue | 10 | 15 | 10 | 1.500x | 1.000 | 5 | 0 | 0 | 0 |
| 03_dependencies | 7 | 12 | 11 | 1.091x | 0.636 | 1 | 0 | 0 | 0 |
| 04_forwarding | 8 | 13 | 9 | 1.444x | 0.889 | 4 | 0 | 0 | 0 |
| 05_branches | 14 | 27 | 26 | 1.038x | 0.538 | 1 | 0 | 0 | 8 |
| 06_jumps | 6 | 15 | 14 | 1.071x | 0.429 | 1 | 0 | 0 | 4 |
| 07_load_store | 16 | 21 | 20 | 1.050x | 0.800 | 1 | 0 | 0 | 0 |
| 08_mul | 6 | 11 | 10 | 1.100x | 0.600 | 1 | 0 | 0 | 0 |
| 09_div | 13 | 90 | 88 | 1.023x | 0.148 | 2 | 0 | 72 | 0 |
| 10_random_mix | 13 | 37 | 34 | 1.088x | 0.382 | 3 | 1 | 18 | 0 |
| 11_stress_dependencies | 10 | 15 | 14 | 1.071x | 0.714 | 1 | 0 | 0 | 0 |
| 12_branch_flush | 15 | 30 | 29 | 1.034x | 0.517 | 1 | 0 | 0 | 10 |
| 13_waw_pairing | 4 | 9 | 8 | 1.125x | 0.500 | 1 | 0 | 0 | 0 |
| 14_x0_invariant | 5 | 10 | 8 | 1.250x | 0.625 | 2 | 0 | 0 | 0 |
| 15_misaligned_load | 1 | 6 | 6 | 1.000x | 0.167 | 0 | 0 | 0 | 0 |
| 16_misaligned_store | 2 | 7 | 6 | 1.167x | 0.333 | 1 | 0 | 0 | 0 |
| 17_ecall | 1 | 6 | 6 | 1.000x | 0.167 | 0 | 0 | 0 | 0 |
| 18_illegal | 1 | 6 | 6 | 1.000x | 0.167 | 0 | 0 | 0 | 0 |
| 19_structural_replay | 10 | 17 | 16 | 1.062x | 0.625 | 1 | 0 | 0 | 2 |
| 20_div_corner_unsigned | 7 | 48 | 47 | 1.021x | 0.149 | 1 | 0 | 36 | 0 |
| 21_branch_outcomes | 32 | 49 | 42 | 1.167x | 0.762 | 7 | 0 | 0 | 12 |
| 22_forwarding_paths | 9 | 14 | 12 | 1.167x | 0.750 | 2 | 0 | 0 | 0 |
| 23_misaligned_jal | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 24_misaligned_jalr | 1 | 6 | 6 | 1.000x | 0.167 | 0 | 0 | 0 | 0 |
| 25_misaligned_branch | 1 | 6 | 6 | 1.000x | 0.167 | 0 | 0 | 0 | 0 |
| 26_precise_trap | 2 | 7 | 6 | 1.167x | 0.333 | 1 | 0 | 0 | 0 |
| 27_illegal_jalr_funct3 | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 28_illegal_branch_funct3 | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 29_illegal_load_funct3 | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 30_illegal_store_funct3 | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 31_illegal_shift_encoding | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 32_illegal_op_encoding | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 33_illegal_system | 0 | 5 | 5 | 1.000x | 0.000 | 0 | 0 | 0 | 0 |
| 34_not_taken_misaligned_branch | 3 | 8 | 8 | 1.000x | 0.375 | 0 | 0 | 0 | 0 |
| 35_jalr_bit0_clear | 3 | 10 | 10 | 1.000x | 0.300 | 0 | 0 | 0 | 2 |
| 36_overflow_wrap | 6 | 11 | 10 | 1.100x | 0.600 | 1 | 0 | 0 | 0 |
| 37_shift_mask | 9 | 14 | 10 | 1.400x | 0.900 | 4 | 0 | 0 | 0 |
| 38_signed_unsigned_extremes | 11 | 18 | 15 | 1.200x | 0.733 | 3 | 0 | 0 | 2 |
| 39_byte_lanes | 12 | 17 | 16 | 1.062x | 0.750 | 1 | 0 | 0 | 0 |
| 40_halfword_upper_lane | 9 | 14 | 13 | 1.077x | 0.692 | 1 | 0 | 0 | 0 |
| 41_mul_corners | 10 | 15 | 14 | 1.071x | 0.714 | 1 | 0 | 0 | 0 |

Random stress: **500/500 timing-model runs completed**, mean 2-wide model IPC **0.615**, mean speedup over forced single-issue model **1.187x**.
