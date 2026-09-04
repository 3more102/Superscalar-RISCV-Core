module core_assertions (
  input logic clk,
  input logic reset_n,
  input logic [31:0] x0_debug,
  input logic issue0,
  input logic issue1,
  input logic pair_raw,
  input logic pair_waw,
  input logic pair_structural,
  input logic redirect,
  input logic dmem_we,
  input logic dmem_re,
  input logic halted,
  input logic commit0_valid,
  input logic commit1_valid,
  input logic commit0_rd_we,
  input logic commit1_rd_we,
  input logic [4:0] commit0_rd,
  input logic [4:0] commit1_rd
);
  // Immediate assertions are intentionally used here for broad simulator
  // compatibility.  Rich temporal properties live under formal/.
  always_ff @(posedge clk) begin
    if (reset_n) begin
      assert (x0_debug == 32'd0)
        else $fatal(1, "ASSERT: x0 changed");
      assert (!issue1 || issue0)
        else $fatal(1, "ASSERT: slot1 issued without slot0");
      assert (!pair_raw || !issue1)
        else $fatal(1, "ASSERT: pair RAW issued");
      assert (!pair_waw || !issue1)
        else $fatal(1, "ASSERT: pair WAW issued");
      assert (!pair_structural || !issue1)
        else $fatal(1, "ASSERT: structurally illegal pair issued");
      assert (!redirect || (!issue0 && !issue1))
        else $fatal(1, "ASSERT: younger issue on redirect");
      assert (!(dmem_we && dmem_re))
        else $fatal(1, "ASSERT: simultaneous read/write on single memory port");
      assert (!commit1_valid || commit0_valid)
        else $fatal(1, "ASSERT: slot1 committed without older slot0");
      assert (!commit0_rd_we || (commit0_rd != 5'd0))
        else $fatal(1, "ASSERT: architectural write to x0 from slot0");
      assert (!commit1_rd_we || (commit1_rd != 5'd0))
        else $fatal(1, "ASSERT: architectural write to x0 from slot1");
      assert (!halted || (!issue0 && !issue1))
        else $fatal(1, "ASSERT: issue while halted");
      assert (!halted || (!commit0_valid && !commit1_valid))
        else $fatal(1, "ASSERT: architectural commit after halt");
      assert (!halted || (!dmem_we && !dmem_re))
        else $fatal(1, "ASSERT: data-memory side effect/access after halt");
    end
  end
endmodule
