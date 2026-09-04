module memory_model #(
  parameter int IMEM_WORDS = 4096,
  parameter int DMEM_BYTES = 65536
) (
  input  logic        clk,
  input  logic [31:0] imem_addr0,
  input  logic [31:0] imem_addr1,
  output logic [31:0] imem_rdata0,
  output logic [31:0] imem_rdata1,
  input  logic [31:0] dmem_addr,
  input  logic [31:0] dmem_wdata,
  input  logic [3:0]  dmem_be,
  input  logic        dmem_we,
  input  logic        dmem_re,
  output logic [31:0] dmem_rdata
);
  logic [31:0] imem [0:IMEM_WORDS-1];
  logic [7:0]  dmem [0:DMEM_BYTES-1];
  integer i;
  string hexfile;

  initial begin
    for (i=0; i<IMEM_WORDS; i=i+1) imem[i] = 32'h0010_0073; // EBREAK fill
    for (i=0; i<DMEM_BYTES; i=i+1) dmem[i] = 8'd0;
    if (!$value$plusargs("HEX=%s", hexfile)) begin
      $display("ERROR: +HEX=<program.hex> required");
      $finish;
    end
    $display("Loading instruction image: %s", hexfile);
    $readmemh(hexfile, imem);
  end

  always_comb begin
    if ((imem_addr0 >> 2) < IMEM_WORDS) imem_rdata0 = imem[imem_addr0[31:2]];
    else imem_rdata0 = 32'h0010_0073;
    if ((imem_addr1 >> 2) < IMEM_WORDS) imem_rdata1 = imem[imem_addr1[31:2]];
    else imem_rdata1 = 32'h0010_0073;

    if ((dmem_addr + 32'd3) < DMEM_BYTES)
      dmem_rdata = {dmem[dmem_addr+3], dmem[dmem_addr+2], dmem[dmem_addr+1], dmem[dmem_addr]};
    else
      dmem_rdata = 32'd0;
  end

  always_ff @(posedge clk) begin
    if (dmem_we && ((dmem_addr + 32'd3) < DMEM_BYTES)) begin
      if (dmem_be[0]) dmem[dmem_addr]   <= dmem_wdata[7:0];
      if (dmem_be[1]) dmem[dmem_addr+1] <= dmem_wdata[15:8];
      if (dmem_be[2]) dmem[dmem_addr+2] <= dmem_wdata[23:16];
      if (dmem_be[3]) dmem[dmem_addr+3] <= dmem_wdata[31:24];
    end
  end
endmodule
