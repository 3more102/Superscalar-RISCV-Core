module dual_issue_unit (
  input  riscv_pkg::decoded_t d0,
  input  riscv_pkg::decoded_t d1,
  input  logic                stall0_external,
  input  logic                stall1_external,
  output logic                issue0,
  output logic                issue1,
  output logic                pair_raw,
  output logic                pair_waw,
  output logic                pair_structural
);
  import riscv_pkg::*;

  logic d0_serial_or_special;

  always_comb begin
    pair_raw = 1'b0;
    pair_waw = 1'b0;
    pair_structural = 1'b0;

    if (d0.valid && d1.valid && d0.rd_write && (d0.rd != 5'd0)) begin
      pair_raw = (d1.rs1_used && (d1.rs1 == d0.rd)) ||
                 (d1.rs2_used && (d1.rs2 == d0.rd));
      pair_waw = d1.rd_write && (d1.rd != 5'd0) && (d1.rd == d0.rd);
    end

    // Baseline policy: lane 1 is an integer-ALU lane only.  Slot 0 may
    // dual-issue only when it is also a simple, non-serializing ALU op.
    d0_serial_or_special = d0.is_branch || d0.is_jal || d0.is_jalr ||
                           d0.is_load || d0.is_store || d0.is_system ||
                           d0.illegal || (d0.mdu_op != MDU_NONE) ||
                           !d0.lane1_eligible;

    if (d1.valid) begin
      pair_structural = d0_serial_or_special || !d1.lane1_eligible ||
                        d1.is_branch || d1.is_jal || d1.is_jalr ||
                        d1.is_load || d1.is_store || d1.is_system ||
                        d1.illegal || (d1.mdu_op != MDU_NONE);
    end

    issue0 = d0.valid && !stall0_external;
    issue1 = issue0 && d1.valid && !stall1_external &&
             !pair_raw && !pair_waw && !pair_structural;
  end
endmodule
