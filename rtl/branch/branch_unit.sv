module branch_unit (
  input  riscv_pkg::branch_op_e op,
  input  logic [31:0] a,
  input  logic [31:0] b,
  output logic taken
);
  import riscv_pkg::*;
  always_comb begin
    unique case (op)
      BR_EQ:   taken = (a == b);
      BR_NE:   taken = (a != b);
      BR_LT:   taken = ($signed(a) < $signed(b));
      BR_GE:   taken = ($signed(a) >= $signed(b));
      BR_LTU:  taken = (a < b);
      BR_GEU:  taken = (a >= b);
      default: taken = 1'b0;
    endcase
  end
endmodule
