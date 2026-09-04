module alu_branch_harness (
  input logic [31:0] a,
  input logic [31:0] b,
  input riscv_pkg::alu_op_e alu_op,
  input riscv_pkg::branch_op_e br_op
);
  import riscv_pkg::*;

  // Primary inputs are unconstrained SAT variables, avoiding dependence on
  // frontend-specific anyconst attribute lowering.
  logic [31:0] y;
  logic taken;

  alu ua(.op(alu_op), .a(a), .b(b), .y(y));
  branch_unit ub(.op(br_op), .a(a), .b(b), .taken(taken));

  always_comb begin
    unique case (alu_op)
      ALU_ADD:    assert(y == a+b);
      ALU_SUB:    assert(y == a-b);
      ALU_SLL:    assert(y == (a << b[4:0]));
      ALU_SLT:    assert(y == (($signed(a)<$signed(b)) ? 32'd1:32'd0));
      ALU_SLTU:   assert(y == ((a<b) ? 32'd1:32'd0));
      ALU_XOR:    assert(y == (a^b));
      ALU_SRL:    assert(y == (a >> b[4:0]));
      ALU_SRA:    assert(y == ($signed(a) >>> b[4:0]));
      ALU_OR:     assert(y == (a|b));
      ALU_AND:    assert(y == (a&b));
      ALU_COPY_B: assert(y == b);
      default: ;
    endcase
    unique case (br_op)
      BR_EQ:  assert(taken == (a==b));
      BR_NE:  assert(taken == (a!=b));
      BR_LT:  assert(taken == ($signed(a)<$signed(b)));
      BR_GE:  assert(taken == ($signed(a)>=$signed(b)));
      BR_LTU: assert(taken == (a<b));
      BR_GEU: assert(taken == (a>=b));
      default: assert(!taken);
    endcase
  end
endmodule
