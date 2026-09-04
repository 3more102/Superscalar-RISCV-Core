module issue_harness (
  input riscv_pkg::decoded_t d0,
  input riscv_pkg::decoded_t d1,
  input logic stall0,
  input logic stall1
);
  import riscv_pkg::*;

  // Primary inputs are unconstrained SAT variables in the direct Yosys proof.
  // This avoids frontend-specific anyconst handling and checks every possible
  // decoded pair and external-stall combination.
  logic issue0, issue1, raw, waw, structural;

  dual_issue_unit dut(
    .d0(d0),
    .d1(d1),
    .stall0_external(stall0),
    .stall1_external(stall1),
    .issue0(issue0),
    .issue1(issue1),
    .pair_raw(raw),
    .pair_waw(waw),
    .pair_structural(structural)
  );

  always_comb begin
    assert (!issue1 || issue0);
    assert (!raw || !issue1);
    assert (!waw || !issue1);
    assert (!structural || !issue1);
    if (stall0) assert (!issue0);
  end
endmodule
