// Closed formal environment for the complete core.
// Reset is constrained low for the first sampled clock and high thereafter;
// instruction/data memory values intentionally remain fully symbolic.
module core_formal_harness(input logic clk);
  (* anyseq *) logic reset_n;
  (* anyseq *) logic [31:0] imem_rdata0;
  (* anyseq *) logic [31:0] imem_rdata1;
  (* anyseq *) logic [31:0] dmem_rdata;

  logic f_seen_clock = 1'b0;
  always_ff @(posedge clk) begin
    if (!f_seen_clock) begin
      assume (!reset_n);
      f_seen_clock <= 1'b1;
    end else begin
      assume (reset_n);
    end
  end

  superscalar_core #(
    .RESET_PC(32'h0000_0000),
    .DIV_LATENCY(2),
    .ENABLE_DUAL_ISSUE(1'b1)
  ) dut (
    .clk(clk),
    .reset_n(reset_n),
    .imem_addr0(), .imem_addr1(),
    .imem_rdata0(imem_rdata0), .imem_rdata1(imem_rdata1),
    .dmem_addr(), .dmem_wdata(), .dmem_be(), .dmem_we(), .dmem_re(),
    .dmem_rdata(dmem_rdata),
    .halted(), .trap_valid(), .trap_pc(), .trap_cause(),
    .commit0_valid(), .commit0_pc(), .commit0_instr(), .commit0_rd_we(),
    .commit0_rd(), .commit0_value(), .commit0_mem_we(), .commit0_mem_addr(),
    .commit0_mem_data(),
    .commit1_valid(), .commit1_pc(), .commit1_instr(), .commit1_rd_we(),
    .commit1_rd(), .commit1_value(),
    .perf_cycles(), .perf_retired(), .perf_dual_issue_cycles(),
    .perf_single_issue_cycles(), .perf_stall_cycles(), .perf_branch_count(),
    .perf_mispredict_count(), .perf_load_use_stalls(), .perf_structural_stalls(),
    .perf_divider_stalls(),
    .x0_debug(), .dbg_issue0(), .dbg_issue1(), .dbg_pair_raw(), .dbg_pair_waw(),
    .dbg_pair_structural(), .dbg_redirect(), .dbg_fwd_ex(), .dbg_fwd_mem(),
    .dbg_fwd_wb()
  );
endmodule
