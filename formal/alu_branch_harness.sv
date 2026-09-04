module alu_branch_harness (
  input  logic [31:0] a,
  input  logic [31:0] b,
  input  riscv_pkg::alu_op_e alu_op,
  input  riscv_pkg::branch_op_e br_op,
  output logic [31:0] actual_y,
  output logic [31:0] expected_y,
  output logic        actual_taken,
  output logic        expected_taken
);
  import riscv_pkg::*;

  // Primary inputs are unconstrained SAT variables.  Keep the DUT and the
  // formal specification structurally separate, then prove only two final
  // equalities.  Exposing actual/expected values as top-level outputs makes
  // any counterexample immediately actionable in the SAT report.
  alu ua(.op(alu_op), .a(a), .b(b), .y(actual_y));
  branch_unit ub(.op(br_op), .a(a), .b(b), .taken(actual_taken));

  always_comb begin
    expected_y = 32'd0;
    case (alu_op)
      ALU_ADD:    expected_y = a + b;
      ALU_SUB:    expected_y = a - b;
      ALU_SLL:    expected_y = a << b[4:0];
      ALU_SLT:    expected_y = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
      ALU_SLTU:   expected_y = (a < b) ? 32'd1 : 32'd0;
      ALU_XOR:    expected_y = a ^ b;
      ALU_SRL:    expected_y = a >> b[4:0];
      ALU_SRA:    expected_y = $signed(a) >>> b[4:0];
      ALU_OR:     expected_y = a | b;
      ALU_AND:    expected_y = a & b;
      ALU_COPY_B: expected_y = b;
      default:    expected_y = 32'd0;
    endcase

    expected_taken = 1'b0;
    case (br_op)
      BR_EQ:   expected_taken = (a == b);
      BR_NE:   expected_taken = (a != b);
      BR_LT:   expected_taken = ($signed(a) < $signed(b));
      BR_GE:   expected_taken = ($signed(a) >= $signed(b));
      BR_LTU:  expected_taken = (a < b);
      BR_GEU:  expected_taken = (a >= b);
      default: expected_taken = 1'b0;
    endcase

    assert (actual_y == expected_y);
    assert (actual_taken == expected_taken);
  end
endmodule
