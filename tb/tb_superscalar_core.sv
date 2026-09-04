`timescale 1ns/1ps
module tb_superscalar_core #(
  parameter bit DUAL_ENABLE = 1'b1
);
  logic clk=0, reset_n=0;
  always #5 clk = ~clk;

  logic [31:0] imem_addr0,imem_addr1,imem_rdata0,imem_rdata1;
  logic [31:0] dmem_addr,dmem_wdata,dmem_rdata; logic [3:0] dmem_be; logic dmem_we,dmem_re;
  logic halted,trap_valid; logic [31:0] trap_pc; logic [3:0] trap_cause;
  logic c0v,c0we,c0mwe,c1v,c1we; logic [31:0] c0pc,c0ins,c0val,c0ma,c0md,c1pc,c1ins,c1val; logic [4:0] c0rd,c1rd;
  logic [63:0] perf_cycles,perf_retired,perf_dual,perf_single,perf_stall,perf_br,perf_misp,perf_lu,perf_struct,perf_div;
  logic [31:0] x0_debug; logic dbg_i0,dbg_i1,dbg_raw,dbg_waw,dbg_struct,dbg_redir,dbg_fwd_ex,dbg_fwd_mem,dbg_fwd_wb;
  integer trace_fd, cov_fd, status_fd; string tracefile,covfile,statusfile; integer cyc=0; integer post_halt=0; logic halt_seen=0;

  integer cov_dual=0,cov_single=0,cov_raw=0,cov_waw=0,cov_struct=0,cov_redirect=0;
  integer cov_load=0,cov_store=0,cov_branch=0,cov_jal=0,cov_jalr=0,cov_op=0,cov_opimm=0,cov_muldiv=0;
  integer cov_fwd_ex=0,cov_fwd_mem=0,cov_fwd_wb=0;

  superscalar_core #(.ENABLE_DUAL_ISSUE(DUAL_ENABLE)) dut (.*,
    .commit0_valid(c0v),.commit0_pc(c0pc),.commit0_instr(c0ins),.commit0_rd_we(c0we),.commit0_rd(c0rd),.commit0_value(c0val),
    .commit0_mem_we(c0mwe),.commit0_mem_addr(c0ma),.commit0_mem_data(c0md),
    .commit1_valid(c1v),.commit1_pc(c1pc),.commit1_instr(c1ins),.commit1_rd_we(c1we),.commit1_rd(c1rd),.commit1_value(c1val),
    .perf_dual_issue_cycles(perf_dual),.perf_single_issue_cycles(perf_single),.perf_stall_cycles(perf_stall),
    .perf_branch_count(perf_br),.perf_mispredict_count(perf_misp),.perf_load_use_stalls(perf_lu),
    .perf_structural_stalls(perf_struct),.perf_divider_stalls(perf_div),
    .dbg_issue0(dbg_i0),.dbg_issue1(dbg_i1),.dbg_pair_raw(dbg_raw),.dbg_pair_waw(dbg_waw),
    .dbg_pair_structural(dbg_struct),.dbg_redirect(dbg_redir),
    .dbg_fwd_ex(dbg_fwd_ex),.dbg_fwd_mem(dbg_fwd_mem),.dbg_fwd_wb(dbg_fwd_wb)
  );

  memory_model mem (.*);
  core_assertions asrt(.clk(clk),.reset_n(reset_n),.x0_debug(x0_debug),.issue0(dbg_i0),.issue1(dbg_i1),
    .pair_raw(dbg_raw),.pair_waw(dbg_waw),.pair_structural(dbg_struct),.redirect(dbg_redir),
    .dmem_we(dmem_we),.dmem_re(dmem_re),.halted(halted),
    .commit0_valid(c0v),.commit1_valid(c1v),.commit0_rd_we(c0we),.commit1_rd_we(c1we),
    .commit0_rd(c0rd),.commit1_rd(c1rd));

  task automatic sample_commit(input logic valid, input integer slot, input logic [31:0] pc, input logic [31:0] ins,
    input logic rdwe,input logic [4:0] rd,input logic [31:0] val,input logic mwe,input logic [31:0] ma,input logic [31:0] md);
    logic [6:0] opc; logic [6:0] f7;
    begin
      if (valid) begin
        $fwrite(trace_fd,"%0d,%0d,%08x,%08x,%0d,%0d,%08x,%0d,%08x,%08x\n",cyc,slot,pc,ins,rdwe,rd,val,mwe,ma,md);
        opc=ins[6:0]; f7=ins[31:25];
        case(opc)
          7'h03: cov_load=cov_load+1;
          7'h23: cov_store=cov_store+1;
          7'h63: cov_branch=cov_branch+1;
          7'h6f: cov_jal=cov_jal+1;
          7'h67: cov_jalr=cov_jalr+1;
          7'h13: cov_opimm=cov_opimm+1;
          7'h33: begin cov_op=cov_op+1; if(f7==7'h01) cov_muldiv=cov_muldiv+1; end
          default: ;
        endcase
      end
    end
  endtask

  initial begin
    if (!$value$plusargs("TRACE=%s",tracefile)) tracefile="commit_trace.csv";
    if (!$value$plusargs("COVERAGE=%s",covfile)) covfile="functional_coverage.txt";
    if (!$value$plusargs("STATUS=%s",statusfile)) statusfile="rtl_status.txt";
    trace_fd=$fopen(tracefile,"w");
    $fwrite(trace_fd,"cycle,slot,pc,instr,rd_we,rd,rd_value,mem_we,mem_addr,mem_data\n");
    repeat(4) @(posedge clk); reset_n <= 1'b1;
  end

  always @(posedge clk) begin
    if (reset_n) begin
      cyc <= cyc+1;
      if (dbg_i0 && dbg_i1) cov_dual <= cov_dual+1;
      else if (dbg_i0) cov_single <= cov_single+1;
      if (dbg_raw) cov_raw <= cov_raw+1;
      if (dbg_waw) cov_waw <= cov_waw+1;
      if (dbg_struct) cov_struct <= cov_struct+1;
      if (dbg_redir) cov_redirect <= cov_redirect+1;
      if (dbg_fwd_ex) cov_fwd_ex <= cov_fwd_ex+1;
      if (dbg_fwd_mem) cov_fwd_mem <= cov_fwd_mem+1;
      if (dbg_fwd_wb) cov_fwd_wb <= cov_fwd_wb+1;
      sample_commit(c0v,0,c0pc,c0ins,c0we,c0rd,c0val,c0mwe,c0ma,c0md);
      sample_commit(c1v,1,c1pc,c1ins,c1we,c1rd,c1val,1'b0,32'd0,32'd0);
      if (halted && !halt_seen) begin
        halt_seen <= 1'b1;
        post_halt <= 0;
      end else if (halt_seen) begin
        post_halt <= post_halt + 1;
        if (post_halt == 2) begin
          cov_fd=$fopen(covfile,"w");
          $fwrite(cov_fd,"dual_issue=%0d\nsingle_issue=%0d\npair_raw=%0d\npair_waw=%0d\nstructural_block=%0d\nredirect=%0d\n",cov_dual,cov_single,cov_raw,cov_waw,cov_struct,cov_redirect);
          $fwrite(cov_fd,"load=%0d\nstore=%0d\nbranch=%0d\njal=%0d\njalr=%0d\nop=%0d\nopimm=%0d\nmuldiv=%0d\n",cov_load,cov_store,cov_branch,cov_jal,cov_jalr,cov_op,cov_opimm,cov_muldiv);
          $fwrite(cov_fd,"forward_ex=%0d\nforward_mem=%0d\nforward_wb=%0d\n",cov_fwd_ex,cov_fwd_mem,cov_fwd_wb);
          $fclose(cov_fd); $fclose(trace_fd);
          status_fd=$fopen(statusfile,"w");
          $fwrite(status_fd,"trap_cause=%0d\n",trap_cause);
          $fwrite(status_fd,"trap_pc=%08x\n",trap_pc);
          $fwrite(status_fd,"cycles=%0d\n",perf_cycles);
          $fwrite(status_fd,"retired=%0d\n",perf_retired);
          $fwrite(status_fd,"dual_issue_cycles=%0d\n",perf_dual);
          $fwrite(status_fd,"single_issue_cycles=%0d\n",perf_single);
          $fwrite(status_fd,"stall_cycles=%0d\n",perf_stall);
          $fwrite(status_fd,"branch_count=%0d\n",perf_br);
          $fwrite(status_fd,"mispredict_count=%0d\n",perf_misp);
          $fwrite(status_fd,"load_use_stalls=%0d\n",perf_lu);
          $fwrite(status_fd,"structural_stalls=%0d\n",perf_struct);
          $fwrite(status_fd,"divider_stalls=%0d\n",perf_div);
          $fclose(status_fd);
          $display("HALT cause=%0d pc=%08x cycles=%0d retired=%0d dual=%0d single=%0d IPC=%f",trap_cause,trap_pc,perf_cycles,perf_retired,perf_dual,perf_single,(perf_cycles?1.0*perf_retired/perf_cycles:0.0));
          $finish;
        end
      end
      if (cyc > 100000) $fatal(1,"TIMEOUT");
    end
  end
endmodule
