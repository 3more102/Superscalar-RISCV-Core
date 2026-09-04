module superscalar_core #(
  parameter logic [31:0] RESET_PC = 32'h0000_0000,
  parameter int DIV_LATENCY = 8,
  parameter bit ENABLE_DUAL_ISSUE = 1'b1
) (
  input  logic        clk,
  input  logic        reset_n,

  output logic [31:0] imem_addr0,
  output logic [31:0] imem_addr1,
  input  logic [31:0] imem_rdata0,
  input  logic [31:0] imem_rdata1,

  output logic [31:0] dmem_addr,
  output logic [31:0] dmem_wdata,
  output logic [3:0]  dmem_be,
  output logic        dmem_we,
  output logic        dmem_re,
  input  logic [31:0] dmem_rdata,

  output logic        halted,
  output logic        trap_valid,
  output logic [31:0] trap_pc,
  output logic [3:0]  trap_cause,

  output logic        commit0_valid,
  output logic [31:0] commit0_pc,
  output logic [31:0] commit0_instr,
  output logic        commit0_rd_we,
  output logic [4:0]  commit0_rd,
  output logic [31:0] commit0_value,
  output logic        commit0_mem_we,
  output logic [31:0] commit0_mem_addr,
  output logic [31:0] commit0_mem_data,

  output logic        commit1_valid,
  output logic [31:0] commit1_pc,
  output logic [31:0] commit1_instr,
  output logic        commit1_rd_we,
  output logic [4:0]  commit1_rd,
  output logic [31:0] commit1_value,

  output logic [63:0] perf_cycles,
  output logic [63:0] perf_retired,
  output logic [63:0] perf_dual_issue_cycles,
  output logic [63:0] perf_single_issue_cycles,
  output logic [63:0] perf_stall_cycles,
  output logic [63:0] perf_branch_count,
  output logic [63:0] perf_mispredict_count,
  output logic [63:0] perf_load_use_stalls,
  output logic [63:0] perf_structural_stalls,
  output logic [63:0] perf_divider_stalls,

  output logic [31:0] x0_debug,
  output logic        dbg_issue0,
  output logic        dbg_issue1,
  output logic        dbg_pair_raw,
  output logic        dbg_pair_waw,
  output logic        dbg_pair_structural,
  output logic        dbg_redirect,
  output logic        dbg_fwd_ex,
  output logic        dbg_fwd_mem,
  output logic        dbg_fwd_wb
);
  import riscv_pkg::*;

  // --------------------------------------------------------------------------
  // Two-entry instruction front-end buffer.
  // next_fetch_pc always points at the first instruction not already buffered.
  // If only slot0 issues, old slot1 is shifted into slot0 and one new word is
  // appended.  This is the replay mechanism for a blocked younger instruction.
  // --------------------------------------------------------------------------
  logic        buf_v0, buf_v1;
  logic [31:0] buf_pc0, buf_pc1;
  logic [31:0] buf_instr0, buf_instr1;
  logic [31:0] next_fetch_pc;

  decoded_t d0, d1;

  assign imem_addr0 = next_fetch_pc;
  assign imem_addr1 = next_fetch_pc + 32'd4;

  decoder u_dec0 (.valid_i(buf_v0), .instr_i(buf_instr0), .pc_i(buf_pc0), .dec_o(d0));
  decoder u_dec1 (.valid_i(buf_v1), .instr_i(buf_instr1), .pc_i(buf_pc1), .dec_o(d1));

  // --------------------------------------------------------------------------
  // Pipeline registers.
  // --------------------------------------------------------------------------
  ex_pipe_t  ex0_q, ex1_q;
  mem_pipe_t mem0_q, mem1_q;
  wb_pipe_t  wb0_q, wb1_q;

  // --------------------------------------------------------------------------
  // Register file and writeback.
  // --------------------------------------------------------------------------
  logic [31:0] rf_r0, rf_r1, rf_r2, rf_r3;
  logic        rf_we0, rf_we1;

  assign rf_we0 = !halted && wb0_q.valid && wb0_q.dec.rd_write && !wb0_q.exc_valid &&
                  (wb0_q.dec.rd != 5'd0);
  assign rf_we1 = !halted && wb1_q.valid && wb1_q.dec.rd_write && !wb1_q.exc_valid &&
                  !wb0_q.exc_valid && (wb1_q.dec.rd != 5'd0);

  register_file u_rf (
    .clk(clk), .reset_n(reset_n),
    .raddr0(d0.rs1), .raddr1(d0.rs2),
    .raddr2(d1.rs1), .raddr3(d1.rs2),
    .rdata0(rf_r0), .rdata1(rf_r1), .rdata2(rf_r2), .rdata3(rf_r3),
    .we0(rf_we0), .waddr0(wb0_q.dec.rd), .wdata0(wb0_q.wb_value),
    .we1(rf_we1), .waddr1(wb1_q.dec.rd), .wdata1(wb1_q.wb_value),
    .x0_debug(x0_debug)
  );

  // --------------------------------------------------------------------------
  // EX combinational datapath.
  // --------------------------------------------------------------------------
  logic [31:0] ex0_a, ex0_b, ex1_a, ex1_b;
  logic [31:0] ex0_alu_y, ex1_alu_y;
  logic [31:0] ex0_mul_y;
  logic        ex0_branch_taken;
  logic [31:0] ex0_eff_addr;
  logic        ex0_misaligned;
  logic        ex0_instr_misaligned;
  logic        ex0_control_taken;
  logic [31:0] ex0_control_target;
  logic        ex0_exc_valid;
  logic [3:0]  ex0_exc_cause;
  logic [31:0] ex0_result;
  logic [31:0] ex1_result;
  logic        redirect_valid;
  logic [31:0] redirect_target;

  function automatic logic is_div_op(input mdu_op_e op);
    begin
      is_div_op = (op == MDU_DIV) || (op == MDU_DIVU) ||
                  (op == MDU_REM) || (op == MDU_REMU);
    end
  endfunction

  function automatic logic is_mul_op(input mdu_op_e op);
    begin
      is_mul_op = (op == MDU_MUL) || (op == MDU_MULH) ||
                  (op == MDU_MULHSU) || (op == MDU_MULHU);
    end
  endfunction

  function automatic logic addr_misaligned(
    input mem_size_e size,
    input logic [31:0] addr
  );
    begin
      unique case (size)
        MEM_B: addr_misaligned = 1'b0;
        MEM_H: addr_misaligned = addr[0];
        MEM_W: addr_misaligned = |addr[1:0];
        default: addr_misaligned = 1'b1;
      endcase
    end
  endfunction

  always_comb begin
    ex0_a = ex0_q.dec.op_a_zero ? 32'd0 :
            ex0_q.dec.op_a_pc   ? ex0_q.dec.pc : ex0_q.op1;
    ex0_b = ex0_q.dec.use_imm ? ex0_q.dec.imm : ex0_q.op2;
    ex1_a = ex1_q.dec.op_a_zero ? 32'd0 :
            ex1_q.dec.op_a_pc   ? ex1_q.dec.pc : ex1_q.op1;
    ex1_b = ex1_q.dec.use_imm ? ex1_q.dec.imm : ex1_q.op2;
    ex0_eff_addr = ex0_q.op1 + ex0_q.dec.imm;
  end

  alu u_alu0 (.op(ex0_q.dec.alu_op), .a(ex0_a), .b(ex0_b), .y(ex0_alu_y));
  alu u_alu1 (.op(ex1_q.dec.alu_op), .a(ex1_a), .b(ex1_b), .y(ex1_alu_y));
  mul_unit u_mul0 (.op(ex0_q.dec.mdu_op), .a(ex0_q.op1), .b(ex0_q.op2), .result(ex0_mul_y));
  branch_unit u_br0 (.op(ex0_q.dec.branch_op), .a(ex0_q.op1), .b(ex0_q.op2), .taken(ex0_branch_taken));

  // --------------------------------------------------------------------------
  // Blocking multi-cycle divider.  The EX stage freezes only while a DIV/REM
  // operation is active.  Older MEM/WB stages continue draining.
  // --------------------------------------------------------------------------
  logic div_start, div_busy, div_done;
  logic [31:0] div_result;
  logic ex_stall;

  assign div_start = ex0_q.valid && is_div_op(ex0_q.dec.mdu_op) &&
                     !div_busy && !div_done;
  assign ex_stall = ex0_q.valid && is_div_op(ex0_q.dec.mdu_op) && !div_done;

  div_unit #(.LATENCY(DIV_LATENCY)) u_div0 (
    .clk(clk), .reset_n(reset_n), .start(div_start),
    .op(ex0_q.dec.mdu_op), .dividend(ex0_q.op1), .divisor(ex0_q.op2),
    .busy(div_busy), .done(div_done), .result(div_result)
  );

  always_comb begin
    ex0_control_taken = 1'b0;
    ex0_control_target = 32'd0;
    if (ex0_q.valid) begin
      if (ex0_q.dec.is_jal) begin
        ex0_control_taken = 1'b1;
        ex0_control_target = ex0_q.dec.pc + ex0_q.dec.imm;
      end else if (ex0_q.dec.is_jalr) begin
        ex0_control_taken = 1'b1;
        ex0_control_target = (ex0_q.op1 + ex0_q.dec.imm) & 32'hffff_fffe;
      end else if (ex0_q.dec.is_branch && ex0_branch_taken) begin
        ex0_control_taken = 1'b1;
        ex0_control_target = ex0_q.dec.pc + ex0_q.dec.imm;
      end
    end
    ex0_instr_misaligned = ex0_q.valid && ex0_control_taken && (|ex0_control_target[1:0]);
  end

  always_comb begin
    ex0_misaligned = ex0_q.valid && (ex0_q.dec.is_load || ex0_q.dec.is_store) &&
                     addr_misaligned(ex0_q.dec.mem_size, ex0_eff_addr);

    ex0_exc_valid = 1'b0;
    ex0_exc_cause = 4'd0;
    if (ex0_q.valid) begin
      if (ex0_q.dec.illegal) begin
        ex0_exc_valid = 1'b1;
        ex0_exc_cause = EXC_ILLEGAL;
      end else if (ex0_q.dec.is_ebreak) begin
        ex0_exc_valid = 1'b1;
        ex0_exc_cause = EXC_BREAKPOINT;
      end else if (ex0_q.dec.is_ecall) begin
        ex0_exc_valid = 1'b1;
        ex0_exc_cause = EXC_ECALL_M;
      end else if (ex0_instr_misaligned) begin
        ex0_exc_valid = 1'b1;
        ex0_exc_cause = EXC_INSTR_MISALIGNED;
      end else if (ex0_misaligned && ex0_q.dec.is_load) begin
        ex0_exc_valid = 1'b1;
        ex0_exc_cause = EXC_LOAD_MISALIGNED;
      end else if (ex0_misaligned && ex0_q.dec.is_store) begin
        ex0_exc_valid = 1'b1;
        ex0_exc_cause = EXC_STORE_MISALIGNED;
      end
    end

    ex0_result = ex0_alu_y;
    if (ex0_q.dec.is_jal || ex0_q.dec.is_jalr)
      ex0_result = ex0_q.dec.pc + 32'd4;
    else if (is_mul_op(ex0_q.dec.mdu_op))
      ex0_result = ex0_mul_y;
    else if (is_div_op(ex0_q.dec.mdu_op))
      ex0_result = div_result;
    else if (ex0_q.dec.is_load || ex0_q.dec.is_store)
      ex0_result = ex0_eff_addr;

    ex1_result = ex1_alu_y;

    redirect_valid = ex0_q.valid && ex0_control_taken && !ex0_exc_valid && !ex_stall;
    redirect_target = ex0_control_target;
  end

  assign dbg_redirect = redirect_valid;

  // --------------------------------------------------------------------------
  // MEM stage.  Baseline has one data-memory port and only lane0 may use it.
  // --------------------------------------------------------------------------
  logic [31:0] lsu_aligned_addr;
  logic [31:0] lsu_store_wdata;
  logic [3:0]  lsu_store_be;
  logic [31:0] lsu_load_value;

  load_store_unit u_lsu (
    .dec(mem0_q.dec), .eff_addr(mem0_q.mem_addr),
    .store_data_raw(mem0_q.store_data), .dmem_rdata(dmem_rdata),
    .aligned_addr(lsu_aligned_addr), .store_wdata(lsu_store_wdata),
    .store_be(lsu_store_be), .load_value(lsu_load_value)
  );

  always_comb begin
    dmem_addr  = lsu_aligned_addr;
    dmem_wdata = lsu_store_wdata;
    dmem_be    = lsu_store_be;
    dmem_we    = !halted && mem0_q.valid && mem0_q.dec.is_store && !mem0_q.exc_valid;
    dmem_re    = !halted && mem0_q.valid && mem0_q.dec.is_load  && !mem0_q.exc_valid;
  end

  // --------------------------------------------------------------------------
  // Forwarding/hazard logic.  ALU/MUL/JAL results are forwardable directly
  // from EX.  A load in EX is the only baseline one-cycle RAW stall; its value
  // becomes forwardable from MEM on the following cycle.
  // --------------------------------------------------------------------------
  logic [31:0] mem0_forward_value;
  logic        ex0_forward_ready;
  logic        d0_load_use_hazard, d1_load_use_hazard;

  assign mem0_forward_value = mem0_q.dec.is_load ? lsu_load_value : mem0_q.result;
  assign ex0_forward_ready = ex0_q.valid && ex0_q.dec.rd_write &&
                             !ex0_q.dec.is_load && !is_div_op(ex0_q.dec.mdu_op) &&
                             !ex0_exc_valid;

  function automatic logic source_waits_for_ex_load(input decoded_t d);
    logic h1, h2;
    begin
      h1 = 1'b0;
      h2 = 1'b0;
      if (d.valid && ex0_q.valid && ex0_q.dec.rd_write &&
          (ex0_q.dec.rd != 5'd0) && (ex0_q.dec.is_load || is_div_op(ex0_q.dec.mdu_op))) begin
        h1 = d.rs1_used && (d.rs1 == ex0_q.dec.rd);
        h2 = d.rs2_used && (d.rs2 == ex0_q.dec.rd);
      end
      source_waits_for_ex_load = h1 || h2;
    end
  endfunction

  localparam logic [1:0] FWD_RF  = 2'd0;
  localparam logic [1:0] FWD_WB  = 2'd1;
  localparam logic [1:0] FWD_MEM = 2'd2;
  localparam logic [1:0] FWD_EX  = 2'd3;

  function automatic logic [1:0] resolve_source(
    input logic [4:0] rs,
    input logic       used
  );
    logic [1:0] src;
    begin
      src = FWD_RF;
      if (used && (rs != 5'd0)) begin
        if (wb0_q.valid && wb0_q.dec.rd_write && !wb0_q.exc_valid && (wb0_q.dec.rd == rs)) src = FWD_WB;
        if (wb1_q.valid && wb1_q.dec.rd_write && !wb1_q.exc_valid && (wb1_q.dec.rd == rs)) src = FWD_WB;
        if (mem0_q.valid && mem0_q.dec.rd_write && !mem0_q.exc_valid && (mem0_q.dec.rd == rs)) src = FWD_MEM;
        if (mem1_q.valid && mem1_q.dec.rd_write && !mem1_q.exc_valid && (mem1_q.dec.rd == rs)) src = FWD_MEM;
        if (ex0_forward_ready && (ex0_q.dec.rd == rs)) src = FWD_EX;
        if (ex1_q.valid && ex1_q.dec.rd_write && (ex1_q.dec.rd != 5'd0) && (ex1_q.dec.rd == rs)) src = FWD_EX;
      end
      resolve_source = src;
    end
  endfunction

  function automatic logic [31:0] resolve_operand(
    input logic [4:0]  rs,
    input logic        used,
    input logic [31:0] rf_value
  );
    logic [31:0] v;
    begin
      v = used ? rf_value : 32'd0;
      if (used && (rs != 5'd0)) begin
        // Oldest to newest; later matches override earlier ones.
        if (wb0_q.valid && wb0_q.dec.rd_write && !wb0_q.exc_valid && (wb0_q.dec.rd == rs))
          v = wb0_q.wb_value;
        if (wb1_q.valid && wb1_q.dec.rd_write && !wb1_q.exc_valid && (wb1_q.dec.rd == rs))
          v = wb1_q.wb_value;
        if (mem0_q.valid && mem0_q.dec.rd_write && !mem0_q.exc_valid && (mem0_q.dec.rd == rs))
          v = mem0_forward_value;
        if (mem1_q.valid && mem1_q.dec.rd_write && !mem1_q.exc_valid && (mem1_q.dec.rd == rs))
          v = mem1_q.result;
        if (ex0_forward_ready && (ex0_q.dec.rd == rs))
          v = ex0_result;
        if (ex1_q.valid && ex1_q.dec.rd_write && (ex1_q.dec.rd != 5'd0) && (ex1_q.dec.rd == rs))
          v = ex1_result;
      end
      resolve_operand = v;
    end
  endfunction

  logic [31:0] d0_op1, d0_op2, d1_op1, d1_op2;
  logic [1:0] d0_src1, d0_src2, d1_src1, d1_src2;
  always_comb begin
    d0_op1 = resolve_operand(d0.rs1, d0.rs1_used, rf_r0);
    d0_op2 = resolve_operand(d0.rs2, d0.rs2_used, rf_r1);
    d1_op1 = resolve_operand(d1.rs1, d1.rs1_used, rf_r2);
    d1_op2 = resolve_operand(d1.rs2, d1.rs2_used, rf_r3);
    d0_src1 = resolve_source(d0.rs1, d0.rs1_used);
    d0_src2 = resolve_source(d0.rs2, d0.rs2_used);
    d1_src1 = resolve_source(d1.rs1, d1.rs1_used);
    d1_src2 = resolve_source(d1.rs2, d1.rs2_used);
    d0_load_use_hazard = source_waits_for_ex_load(d0);
    d1_load_use_hazard = source_waits_for_ex_load(d1);
  end

  logic serializing_inflight;
  always_comb begin
    serializing_inflight = 1'b0;
    if (ex0_exc_valid)
      serializing_inflight = 1'b1;
    if (mem0_q.valid && mem0_q.exc_valid)
      serializing_inflight = 1'b1;
    if (wb0_q.valid && wb0_q.exc_valid)
      serializing_inflight = 1'b1;
  end

  // --------------------------------------------------------------------------
  // Dual issue decision.
  // --------------------------------------------------------------------------
  logic issue0, issue1;
  logic pair_raw, pair_waw, pair_structural;
  logic stall0_external, stall1_external;

  assign stall0_external = halted || ex_stall || redirect_valid ||
                           serializing_inflight || d0_load_use_hazard;
  assign stall1_external = halted || ex_stall || redirect_valid ||
                           serializing_inflight || d1_load_use_hazard || !ENABLE_DUAL_ISSUE;

  dual_issue_unit u_issue (
    .d0(d0), .d1(d1),
    .stall0_external(stall0_external),
    .stall1_external(stall1_external),
    .issue0(issue0), .issue1(issue1),
    .pair_raw(pair_raw), .pair_waw(pair_waw), .pair_structural(pair_structural)
  );

  assign dbg_issue0 = issue0;
  assign dbg_issue1 = issue1;
  assign dbg_pair_raw = pair_raw;
  assign dbg_pair_waw = pair_waw;
  assign dbg_pair_structural = pair_structural;
  assign dbg_fwd_ex = (issue0 && ((d0_src1 == FWD_EX) || (d0_src2 == FWD_EX))) ||
                      (issue1 && ((d1_src1 == FWD_EX) || (d1_src2 == FWD_EX)));
  assign dbg_fwd_mem = (issue0 && ((d0_src1 == FWD_MEM) || (d0_src2 == FWD_MEM))) ||
                       (issue1 && ((d1_src1 == FWD_MEM) || (d1_src2 == FWD_MEM)));
  assign dbg_fwd_wb = (issue0 && ((d0_src1 == FWD_WB) || (d0_src2 == FWD_WB))) ||
                      (issue1 && ((d1_src1 == FWD_WB) || (d1_src2 == FWD_WB)));

  // --------------------------------------------------------------------------
  // Front-end state / replay / redirect.
  // --------------------------------------------------------------------------
  always_ff @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      buf_v0 <= 1'b0;
      buf_v1 <= 1'b0;
      buf_pc0 <= 32'd0;
      buf_pc1 <= 32'd0;
      buf_instr0 <= 32'h0000_0013;
      buf_instr1 <= 32'h0000_0013;
      next_fetch_pc <= RESET_PC;
    end else if (redirect_valid) begin
      buf_v0 <= 1'b0;
      buf_v1 <= 1'b0;
      next_fetch_pc <= redirect_target;
    end else if (!halted) begin
      if (!buf_v0) begin
        buf_v0 <= 1'b1;
        buf_v1 <= 1'b1;
        buf_pc0 <= next_fetch_pc;
        buf_pc1 <= next_fetch_pc + 32'd4;
        buf_instr0 <= imem_rdata0;
        buf_instr1 <= imem_rdata1;
        next_fetch_pc <= next_fetch_pc + 32'd8;
      end else if (issue0 && issue1) begin
        buf_v0 <= 1'b1;
        buf_v1 <= 1'b1;
        buf_pc0 <= next_fetch_pc;
        buf_pc1 <= next_fetch_pc + 32'd4;
        buf_instr0 <= imem_rdata0;
        buf_instr1 <= imem_rdata1;
        next_fetch_pc <= next_fetch_pc + 32'd8;
      end else if (issue0) begin
        buf_v0 <= buf_v1;
        buf_pc0 <= buf_pc1;
        buf_instr0 <= buf_instr1;
        buf_v1 <= 1'b1;
        buf_pc1 <= next_fetch_pc;
        buf_instr1 <= imem_rdata0;
        next_fetch_pc <= next_fetch_pc + 32'd4;
      end
    end
  end

  // --------------------------------------------------------------------------
  // EX->MEM and MEM->WB combinational records.
  // --------------------------------------------------------------------------
  mem_pipe_t ex0_to_mem, ex1_to_mem;
  wb_pipe_t  mem0_to_wb, mem1_to_wb;

  always_comb begin
    ex0_to_mem = '0;
    ex0_to_mem.valid = ex0_q.valid;
    ex0_to_mem.dec = ex0_q.dec;
    ex0_to_mem.result = ex0_result;
    ex0_to_mem.mem_addr = ex0_eff_addr;
    ex0_to_mem.store_data = ex0_q.store_data;
    ex0_to_mem.exc_valid = ex0_exc_valid;
    ex0_to_mem.exc_cause = ex0_exc_cause;

    ex1_to_mem = '0;
    ex1_to_mem.valid = ex1_q.valid;
    ex1_to_mem.dec = ex1_q.dec;
    ex1_to_mem.result = ex1_result;

    mem0_to_wb = '0;
    mem0_to_wb.valid = mem0_q.valid;
    mem0_to_wb.dec = mem0_q.dec;
    mem0_to_wb.wb_value = mem0_q.dec.is_load ? lsu_load_value : mem0_q.result;
    mem0_to_wb.mem_addr = mem0_q.mem_addr;
    mem0_to_wb.store_data = mem0_q.store_data;
    mem0_to_wb.mem_write = mem0_q.dec.is_store && !mem0_q.exc_valid;
    mem0_to_wb.exc_valid = mem0_q.exc_valid;
    mem0_to_wb.exc_cause = mem0_q.exc_cause;

    mem1_to_wb = '0;
    mem1_to_wb.valid = mem1_q.valid;
    mem1_to_wb.dec = mem1_q.dec;
    mem1_to_wb.wb_value = mem1_q.result;
    mem1_to_wb.exc_valid = mem1_q.exc_valid;
    mem1_to_wb.exc_cause = mem1_q.exc_cause;
  end

  // --------------------------------------------------------------------------
  // Pipeline register movement.
  // --------------------------------------------------------------------------
  always_ff @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      ex0_q <= '0;
      ex1_q <= '0;
      mem0_q <= '0;
      mem1_q <= '0;
      wb0_q <= '0;
      wb1_q <= '0;
      halted <= 1'b0;
      trap_valid <= 1'b0;
      trap_pc <= 32'd0;
      trap_cause <= 4'd0;
    end else begin
      trap_valid <= 1'b0;

      // Oldest stages always drain.
      wb0_q <= mem0_to_wb;
      wb1_q <= mem1_to_wb;

      if (ex_stall) begin
        // DIV/REM owns EX until done. Insert bubbles behind it while MEM/WB drain.
        mem0_q <= '0;
        mem1_q <= '0;
        ex0_q <= ex0_q;
        ex1_q <= ex1_q;
      end else begin
        mem0_q <= ex0_to_mem;
        mem1_q <= ex1_to_mem;

        ex0_q <= '0;
        ex1_q <= '0;
        if (issue0) begin
          ex0_q.valid <= 1'b1;
          ex0_q.dec <= d0;
          ex0_q.op1 <= d0_op1;
          ex0_q.op2 <= d0_op2;
          ex0_q.store_data <= d0_op2;
        end
        if (issue1) begin
          ex1_q.valid <= 1'b1;
          ex1_q.dec <= d1;
          ex1_q.op1 <= d1_op1;
          ex1_q.op2 <= d1_op2;
          ex1_q.store_data <= d1_op2;
        end
      end

      if (wb0_q.valid && wb0_q.exc_valid) begin
        halted <= 1'b1;
        trap_valid <= 1'b1;
        trap_pc <= wb0_q.dec.pc;
        trap_cause <= wb0_q.exc_cause;
      end
    end
  end

  // --------------------------------------------------------------------------
  // Architectural commit trace outputs.
  // --------------------------------------------------------------------------
  always_comb begin
    commit0_valid = !halted && wb0_q.valid && !wb0_q.exc_valid;
    commit0_pc = wb0_q.dec.pc;
    commit0_instr = wb0_q.dec.instr;
    commit0_rd_we = commit0_valid && wb0_q.dec.rd_write && (wb0_q.dec.rd != 5'd0);
    // Normalize architecturally inactive writeback fields.  The commit trace
    // is a public verification interface, so non-writing instructions must not
    // expose encoding residue from instr[11:7] or datapath don't-care values.
    commit0_rd = commit0_rd_we ? wb0_q.dec.rd : 5'd0;
    commit0_value = commit0_rd_we ? wb0_q.wb_value : 32'd0;
    commit0_mem_we = commit0_valid && wb0_q.mem_write;
    commit0_mem_addr = wb0_q.mem_addr;
    commit0_mem_data = wb0_q.store_data;

    commit1_valid = !halted && wb1_q.valid && !wb1_q.exc_valid && !wb0_q.exc_valid;
    commit1_pc = wb1_q.dec.pc;
    commit1_instr = wb1_q.dec.instr;
    commit1_rd_we = commit1_valid && wb1_q.dec.rd_write && (wb1_q.dec.rd != 5'd0);
    commit1_rd = commit1_rd_we ? wb1_q.dec.rd : 5'd0;
    commit1_value = commit1_rd_we ? wb1_q.wb_value : 32'd0;
  end

  // --------------------------------------------------------------------------
  // Performance counters.  Static-not-taken predictor: each taken conditional
  // branch and each JAL/JALR redirect counts as a misprediction/redirect cost.
  // --------------------------------------------------------------------------
  always_ff @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      perf_cycles <= 64'd0;
      perf_retired <= 64'd0;
      perf_dual_issue_cycles <= 64'd0;
      perf_single_issue_cycles <= 64'd0;
      perf_stall_cycles <= 64'd0;
      perf_branch_count <= 64'd0;
      perf_mispredict_count <= 64'd0;
      perf_load_use_stalls <= 64'd0;
      perf_structural_stalls <= 64'd0;
      perf_divider_stalls <= 64'd0;
    end else if (!halted) begin
      perf_cycles <= perf_cycles + 64'd1;
      perf_retired <= perf_retired + (commit0_valid ? 64'd1 : 64'd0) +
                      (commit1_valid ? 64'd1 : 64'd0);

      if (issue0 && issue1)
        perf_dual_issue_cycles <= perf_dual_issue_cycles + 64'd1;
      else if (issue0)
        perf_single_issue_cycles <= perf_single_issue_cycles + 64'd1;
      else if (buf_v0)
        perf_stall_cycles <= perf_stall_cycles + 64'd1;

      if (d0_load_use_hazard && buf_v0)
        perf_load_use_stalls <= perf_load_use_stalls + 64'd1;
      if (issue0 && buf_v1 && !issue1 && pair_structural)
        perf_structural_stalls <= perf_structural_stalls + 64'd1;
      if (ex_stall)
        perf_divider_stalls <= perf_divider_stalls + 64'd1;

      if (ex0_q.valid && ex0_q.dec.is_branch && !ex_stall && !ex0_exc_valid) begin
        perf_branch_count <= perf_branch_count + 64'd1;
        if (ex0_branch_taken)
          perf_mispredict_count <= perf_mispredict_count + 64'd1;
      end else if (ex0_q.valid && (ex0_q.dec.is_jal || ex0_q.dec.is_jalr) && !ex_stall && !ex0_exc_valid) begin
        perf_branch_count <= perf_branch_count + 64'd1;
        perf_mispredict_count <= perf_mispredict_count + 64'd1;
      end
    end
  end

`ifdef FORMAL
  // Open-source formal invariants are kept in-module as immediate assertions.
  // The companion formal/core_harness.sv constrains reset, while instruction
  // and data inputs remain symbolic.  These properties target ordering,
  // replay, precise exceptions and the baseline lane/resource policy.
  logic        f_prev_ex0_advance, f_prev_ex1_advance;
  logic [31:0] f_prev_ex0_pc, f_prev_ex1_pc;
  logic        f_prev_replay;
  logic [31:0] f_prev_buf1_pc, f_prev_buf1_instr;
  logic        f_prev_redirect;
  logic [31:0] f_prev_redirect_target;
  logic        f_prev_issue0, f_prev_issue1;
  logic [31:0] f_prev_issue0_pc, f_prev_issue1_pc;

  always_ff @(posedge clk) begin
    if (!reset_n) begin
      f_prev_ex0_advance <= 1'b0;
      f_prev_ex1_advance <= 1'b0;
      f_prev_ex0_pc <= 32'd0;
      f_prev_ex1_pc <= 32'd0;
      f_prev_replay <= 1'b0;
      f_prev_buf1_pc <= 32'd0;
      f_prev_buf1_instr <= 32'd0;
      f_prev_redirect <= 1'b0;
      f_prev_redirect_target <= 32'd0;
      f_prev_issue0 <= 1'b0;
      f_prev_issue1 <= 1'b0;
      f_prev_issue0_pc <= 32'd0;
      f_prev_issue1_pc <= 32'd0;
    end else begin
      // Architectural and issue invariants.
      assert (x0_debug == 32'd0);
      assert (!issue1 || issue0);
      assert (!pair_raw || !issue1);
      assert (!pair_waw || !issue1);
      assert (!pair_structural || !issue1);
      assert (!redirect_valid || (!issue0 && !issue1));
      assert (!(dmem_we && dmem_re));
      assert (!commit1_valid || commit0_valid);
      assert (!rf_we0 || (wb0_q.dec.rd != 5'd0));
      assert (!rf_we1 || (wb1_q.dec.rd != 5'd0));

      // Front-end is a consecutive, 32-bit-aligned two-entry queue.  This is
      // what makes slot1 replay lossless when only the older slot issues.
      assert (!buf_v1 || buf_v0);
      if (buf_v0)
        assert (buf_pc0[1:0] == 2'b00);
      if (buf_v1) begin
        assert (buf_pc1[1:0] == 2'b00);
        assert (buf_pc1 == buf_pc0 + 32'd4);
      end
      assert (next_fetch_pc[1:0] == 2'b00);
      if (issue1)
        assert (d1.pc == d0.pc + 32'd4);

      // Lane1 is deliberately side-effect-free except for integer register
      // writes.  All control flow, memory, system and M-extension work stays
      // on lane0 in the baseline core.
      if (ex1_q.valid) begin
        assert (ex1_q.dec.lane1_eligible);
        assert (!ex1_q.dec.is_branch && !ex1_q.dec.is_jal && !ex1_q.dec.is_jalr);
        assert (!ex1_q.dec.is_load && !ex1_q.dec.is_store);
        assert (!ex1_q.dec.is_system && !ex1_q.dec.illegal);
        assert (ex1_q.dec.mdu_op == MDU_NONE);
      end
      if (mem1_q.valid) begin
        assert (!mem1_q.dec.is_load && !mem1_q.dec.is_store);
        assert (!mem1_q.exc_valid);
      end
      if (wb1_q.valid)
        assert (!wb1_q.exc_valid);

      // Any lane0 exception must be precise: no same-age younger lane1 entry
      // may accompany it, and no younger memory access may survive ahead of
      // the trap becoming architectural.
      if (ex0_exc_valid)
        assert (!ex1_q.valid);
      if (mem0_q.valid && mem0_q.exc_valid)
        assert (!mem1_q.valid);
      if (wb0_q.valid && wb0_q.exc_valid) begin
        assert (!wb1_q.valid);
        assert (!dmem_we && !dmem_re);
      end
      if (dmem_we)
        assert (mem0_q.valid && mem0_q.dec.is_store && !mem0_q.exc_valid && !halted);
      if (dmem_re)
        assert (mem0_q.valid && mem0_q.dec.is_load && !mem0_q.exc_valid && !halted);
      if (commit0_mem_we)
        assert (commit0_valid && wb0_q.dec.is_store && !wb0_q.exc_valid);

      if (halted) begin
        assert (!commit0_valid && !commit1_valid);
        assert (!rf_we0 && !rf_we1);
        assert (!dmem_we && !dmem_re);
        assert (!issue0 && !issue1);
      end
      if (ex0_q.valid && is_div_op(ex0_q.dec.mdu_op) && !div_done)
        assert (ex_stall);

      // Temporal movement/ordering checks.
      if (f_prev_ex0_advance)
        assert (mem0_q.valid && (mem0_q.dec.pc == f_prev_ex0_pc));
      if (f_prev_ex1_advance)
        assert (mem1_q.valid && (mem1_q.dec.pc == f_prev_ex1_pc));
      if (f_prev_issue0)
        assert (ex0_q.valid && (ex0_q.dec.pc == f_prev_issue0_pc));
      if (f_prev_issue1)
        assert (ex1_q.valid && (ex1_q.dec.pc == f_prev_issue1_pc));
      if (f_prev_replay) begin
        assert (buf_v0);
        assert (buf_pc0 == f_prev_buf1_pc);
        assert (buf_instr0 == f_prev_buf1_instr);
      end
      if (f_prev_redirect) begin
        assert (!buf_v0 && !buf_v1);
        assert (next_fetch_pc == f_prev_redirect_target);
      end

      f_prev_ex0_advance <= ex0_q.valid && !ex_stall;
      f_prev_ex1_advance <= ex1_q.valid && !ex_stall;
      f_prev_ex0_pc <= ex0_q.dec.pc;
      f_prev_ex1_pc <= ex1_q.dec.pc;
      f_prev_replay <= issue0 && !issue1 && buf_v1 && !redirect_valid;
      f_prev_buf1_pc <= buf_pc1;
      f_prev_buf1_instr <= buf_instr1;
      f_prev_redirect <= redirect_valid;
      f_prev_redirect_target <= redirect_target;
      f_prev_issue0 <= issue0;
      f_prev_issue1 <= issue1;
      f_prev_issue0_pc <= d0.pc;
      f_prev_issue1_pc <= d1.pc;
    end
  end
`endif

endmodule
