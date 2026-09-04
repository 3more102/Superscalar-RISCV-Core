module issue_harness;
  import riscv_pkg::*;

  // Unconstrained symbolic inputs for exhaustive dual-issue checking.
  // Plain undriven internal signals are treated as X constants by the
  // Yosys-Slang SAT flow; anyconst makes them formal variables instead.
  (* anyconst *) decoded_t d0, d1;
  (* anyconst *) logic stall0, stall1;

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
