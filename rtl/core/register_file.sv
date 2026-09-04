module register_file (
  input  logic        clk,
  input  logic        reset_n,
  input  logic [4:0]  raddr0,
  input  logic [4:0]  raddr1,
  input  logic [4:0]  raddr2,
  input  logic [4:0]  raddr3,
  output logic [31:0] rdata0,
  output logic [31:0] rdata1,
  output logic [31:0] rdata2,
  output logic [31:0] rdata3,
  input  logic        we0,
  input  logic [4:0]  waddr0,
  input  logic [31:0] wdata0,
  input  logic        we1,
  input  logic [4:0]  waddr1,
  input  logic [31:0] wdata1,
  output logic [31:0] x0_debug
);
  logic [31:0] regs [0:31];
  integer i;

  always_comb begin
    rdata0 = (raddr0 == 5'd0) ? 32'd0 : regs[raddr0];
    rdata1 = (raddr1 == 5'd0) ? 32'd0 : regs[raddr1];
    rdata2 = (raddr2 == 5'd0) ? 32'd0 : regs[raddr2];
    rdata3 = (raddr3 == 5'd0) ? 32'd0 : regs[raddr3];
    x0_debug = regs[0];
  end

  always_ff @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      for (i = 0; i < 32; i = i + 1)
        regs[i] <= 32'd0;
    end else begin
      if (we0 && (waddr0 != 5'd0))
        regs[waddr0] <= wdata0;
      if (we1 && (waddr1 != 5'd0))
        regs[waddr1] <= wdata1;
      regs[0] <= 32'd0;
    end
  end
endmodule
