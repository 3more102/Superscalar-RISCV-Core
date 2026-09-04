module mul_unit (
  input  riscv_pkg::mdu_op_e op,
  input  logic [31:0] a,
  input  logic [31:0] b,
  output logic [31:0] result
);
  import riscv_pkg::*;
  logic signed [63:0] prod_ss;
  logic        [63:0] prod_uu;
  logic signed [32:0] a_ext;
  logic signed [32:0] b_ext;
  logic signed [65:0] prod_su;

  always_comb begin
    prod_ss = $signed(a) * $signed(b);
    prod_uu = $unsigned(a) * $unsigned(b);
    a_ext = {a[31], a};
    b_ext = {1'b0, b};
    prod_su = a_ext * b_ext;

    unique case (op)
      MDU_MUL:    result = prod_uu[31:0];
      MDU_MULH:   result = prod_ss[63:32];
      MDU_MULHSU: result = prod_su[63:32];
      MDU_MULHU:  result = prod_uu[63:32];
      default:    result = 32'd0;
    endcase
  end
endmodule
